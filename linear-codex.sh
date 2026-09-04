#!/usr/bin/env bash
set -euo pipefail

# linear-codex.sh
#
# Minimal one-file workflow helper for Linear -> Codex -> review -> Linear.
#
# Commands:
#   ./linear-codex.sh next
#   ./linear-codex.sh start DHA-15
#   ./linear-codex.sh finish DHA-15
#
# Requirements:
#   curl, jq, git, codex
#
# Environment:
#   LINEAR_API_KEY       Required for Linear reads/writes
#   LINEAR_PROJECT       Default: noxyn-solari
#   LINEAR_TEAM_KEY      Default: DHA
#   CODEX_MODEL          Optional model override
#   CODEX_EXTRA_ARGS     Optional extra args passed to `codex exec`
#   CHECK_CMD            Optional validation command used by `finish`
#
# Notes:
# - Your ChatGPT Linear connector is separate from this local script.
#   The shell script needs a normal Linear personal API key.
# - `start` creates/reuses one worktree per Linear issue.
# - `start` launches a fresh non-interactive Codex run with `codex exec`.
# - `finish` never pushes.
# - `finish` asks before committing and before marking the issue Done.

LINEAR_API_URL="${LINEAR_API_URL:-https://api.linear.app/graphql}"
LINEAR_PROJECT="${LINEAR_PROJECT:-noxyn-solari}"
LINEAR_TEAM_KEY="${LINEAR_TEAM_KEY:-DHA}"
CODEX_EXTRA_ARGS="${CODEX_EXTRA_ARGS:-}"
CODEX_MODEL="${CODEX_MODEL:-gpt-5.6-terra}"
CODEX_MODEL_REASONING="${CODEX_MODEL_REASONING:-medium}"

die() {
  echo "error: $*" >&2
  exit 1
}

need() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

need curl
need jq
need git

require_linear_key() {
  [[ -n "${LINEAR_API_KEY:-}" ]] || die \
    "LINEAR_API_KEY is not set. Export a Linear personal API key first."
}

linear_graphql() {
  require_linear_key

  local query="$1"
  local variables="${2-}"

  if [[ -z "$variables" ]]; then
    variables='{}'
  fi

  # Validate variables explicitly before building the request. This avoids the
  # brittle `jq --argjson` failure mode and gives a useful error if a caller
  # ever passes malformed JSON.
  if ! jq -e . >/dev/null 2>&1 <<<"$variables"; then
    echo "error: malformed Linear GraphQL variables JSON:" >&2
    printf '%s\n' "$variables" >&2
    return 1
  fi

  local payload
  payload="$(
    jq -cn \
      --arg q "$query" \
      --arg variables "$variables" \
      '{query:$q, variables:($variables | fromjson)}'
  )"

  local response
  response="$(
    curl -fsS "$LINEAR_API_URL" \
      -H "Authorization: ${LINEAR_API_KEY}" \
      -H "Content-Type: application/json" \
      --data-binary "$payload"
  )"

  jq -e '
    if .errors
    then error(.errors | tostring)
    else .data
    end
  ' <<<"$response"
}

repo_root() {
  git rev-parse --show-toplevel 2>/dev/null ||
    die "run this from inside the repository"
}

slugify() {
  tr '[:upper:]' '[:lower:]' |
    sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//; s/-+/-/g'
}

fetch_issue() {
  local id="$1"

  linear_graphql \
    'query($id:String!){
      issue(id:$id){
        id
        identifier
        title
        description
        url
        priority
        state { id name type }
        project { id name }
        projectMilestone { id name }
        relations {
          nodes {
            type
            relatedIssue {
              id
              identifier
              title
              state { name type }
            }
          }
        }
      }
    }' \
    "$(jq -cn --arg id "$id" '{id:$id}')"
}

find_project_id() {
  local project_name="$1"

  linear_graphql \
    'query($name:String!){
      projects(filter:{name:{eq:$name}}, first:10){
        nodes { id name }
      }
    }' \
    "$(jq -cn --arg name "$project_name" '{name:$name}')" |
    jq -r '.projects.nodes[0].id // empty'
}

list_candidate_issues() {
  local project_id="$1"

  linear_graphql \
    'query($projectId:ID!){
      issues(
        first:100
        filter:{
          project:{id:{eq:$projectId}}
          state:{type:{in:["unstarted","backlog"]}}
        }
      ){
        nodes {
          id
          identifier
          title
          priority
          createdAt
          state { name type }
          projectMilestone { name }
          relations {
            nodes {
              type
              relatedIssue {
                identifier
                title
                state { name type }
              }
            }
          }
        }
      }
    }' \
    "$(jq -cn --arg projectId "$project_id" '{projectId:$projectId}')"
}

cmd_next() {
  local project_id
  project_id="$(find_project_id "$LINEAR_PROJECT")"
  [[ -n "$project_id" ]] || die "Linear project not found: $LINEAR_PROJECT"

  local data
  data="$(list_candidate_issues "$project_id")"

  local candidates
  candidates="$(
    jq '
      def blockers:
        [
          (.relations.nodes // [])[]
          | select(.type == "blocked_by")
          | .relatedIssue
          | select(
              (.state.type // "") != "completed"
              and (.state.type // "") != "canceled"
            )
        ];

      .issues.nodes
      | map(select((blockers | length) == 0))
      | sort_by(
          if .priority == 1 then 0
          elif .priority == 2 then 1
          elif .priority == 3 then 2
          elif .priority == 4 then 3
          else 4
          end,
          .createdAt
        )
    ' <<<"$data"
  )"

  local count
  count="$(jq 'length' <<<"$candidates")"

  if [[ "$count" -eq 0 ]]; then
    echo "No unblocked Todo/Backlog issues found in project: $LINEAR_PROJECT"
    exit 0
  fi

  echo "Next unblocked issues in $LINEAR_PROJECT:"
  jq -r '
    .[] |
    "- \(.identifier) — \(.title) [\(.state.name)]" +
    (if .projectMilestone then " — \(.projectMilestone.name)" else "" end)
  ' <<<"$candidates"

  echo
  echo "Suggested next:"
  jq -r '.[0] | "\(.identifier) — \(.title)"' <<<"$candidates"
}

build_prompt() {
  local issue_json="$1"

  local identifier
  local title
  local description

  identifier="$(jq -r '.issue.identifier' <<<"$issue_json")"
  title="$(jq -r '.issue.title' <<<"$issue_json")"
  description="$(jq -r '.issue.description // ""' <<<"$issue_json")"

  cat <<EOF
Implement Linear issue ${identifier} only:

${identifier} — ${title}

The Linear issue body is the implementation contract.

--- LINEAR ISSUE START ---

${description}

--- LINEAR ISSUE END ---

## Workflow rules

1. Read \`AGENTS.md\` first.
2. Keep investigation narrow.
3. Use \`rg\` / \`rg --files\` to locate the existing implementation.
4. Prefer extending existing contracts and patterns over introducing new abstractions.
5. Do not broadly inspect historical phase reports, unrelated docs, or unrelated code.
6. Do not load skills/documentation unless they are actually relevant to files you need to change.
7. Do not perform unrelated refactors, cleanup, formatting, or design work.
8. Do not modify work that belongs to another Linear issue.
9. If the implementation requires a substantive change outside this issue's stated scope, STOP and explain before making it.
10. Preserve unrelated existing user changes.
11. Run the narrowest relevant tests/checks first.
12. Do not push.
13. Do not continue to another issue.

## Before editing

Briefly report:

- the existing implementation path you found
- the exact files/areas you expect to modify
- why each is necessary

Keep that report short, then implement the issue.

## Completion report

At completion report:

- files changed
- behavior implemented
- API/schema/generated-client changes, if any
- tests/checks actually run and results
- anything not verified
- unresolved concerns
- whether anything went outside the intended issue scope

STOP after ${identifier}.
EOF
}

find_issue_worktree() {
  local identifier="$1"

  local root
  local parent
  local guessed

  root="$(repo_root)"
  parent="$(dirname "$root")"
  guessed="${parent}/$(basename "$root")-${identifier}"

  if [[ -d "$guessed" ]]; then
    printf '%s\n' "$guessed"
    return
  fi

  git worktree list --porcelain |
    awk -v id="$identifier" '
      /^worktree / {
        path = substr($0, 10)
      }
      /^branch / && tolower($0) ~ tolower(id) {
        print path
        exit
      }
    '
}

launch_codex() {
  local prompt_file="$1"

  need codex

  local prompt
  prompt="$(cat "$prompt_file")"

  if [[ -n "${CODEX_MODEL:-}" ]]; then
    # Intentionally allow word splitting for CODEX_EXTRA_ARGS.
    # shellcheck disable=SC2086
    codex exec --model "$CODEX_MODEL" -c "model_reasoning_effort=$CODEX_MODEL_REASONING" $CODEX_EXTRA_ARGS "$prompt"
  else
    # shellcheck disable=SC2086
    codex exec $CODEX_EXTRA_ARGS "$prompt"
  fi
}

cmd_start() {
  local issue="${1:-}"
  [[ -n "$issue" ]] || die "usage: $0 start DHA-15"

  local root
  root="$(repo_root)"
  cd "$root"

  local issue_json
  issue_json="$(fetch_issue "$issue")"

  local identifier
  local title
  local state_type

  identifier="$(jq -r '.issue.identifier // empty' <<<"$issue_json")"
  title="$(jq -r '.issue.title // empty' <<<"$issue_json")"
  state_type="$(jq -r '.issue.state.type // empty' <<<"$issue_json")"

  [[ -n "$identifier" ]] || die "issue not found: $issue"

  if [[ "$state_type" == "completed" ]]; then
    die "$identifier is already Done in Linear"
  fi

  if [[ "$state_type" == "canceled" ]]; then
    die "$identifier is canceled in Linear"
  fi

  local slug
  local branch
  local parent
  local worktree
  local prompt_file

  slug="$(printf '%s' "$title" | slugify | cut -c1-48)"
  branch="$(printf '%s-%s' "$identifier" "$slug" | tr '[:upper:]' '[:lower:]')"

  parent="$(dirname "$root")"
  worktree="${parent}/$(basename "$root")-${identifier}"
  prompt_file="/tmp/${identifier}-codex-prompt.md"

  echo "Issue:    $identifier — $title"
  echo "Branch:   $branch"
  echo "Worktree: $worktree"

  if [[ -d "$worktree" ]]; then
    echo "Using existing worktree: $worktree"
  else
    git worktree add "$worktree" -b "$branch"
  fi

  build_prompt "$issue_json" > "$prompt_file"

  echo
  echo "Prompt saved to: $prompt_file"
  echo "Launching a fresh Codex exec run..."
  echo

  cd "$worktree"
  launch_codex "$prompt_file"
}

linear_done_state_id() {
  local team_key="$1"

  linear_graphql \
    'query($key:String!){
      teams(filter:{key:{eq:$key}}, first:5){
        nodes {
          id
          key
          states {
            nodes { id name type }
          }
        }
      }
    }' \
    "$(jq -cn --arg key "$team_key" '{key:$key}')" |
    jq -r '
      .teams.nodes[0].states.nodes[]
      | select(.type == "completed")
      | .id
    ' |
    head -n1
}

mark_issue_done() {
  local issue_uuid="$1"
  local state_id="$2"

  linear_graphql \
    'mutation($id:String!,$stateId:String!){
      issueUpdate(id:$id,input:{stateId:$stateId}){
        success
        issue {
          identifier
          state { name type }
        }
      }
    }' \
    "$(jq -cn \
      --arg id "$issue_uuid" \
      --arg stateId "$state_id" \
      '{id:$id,stateId:$stateId}')"
}

add_linear_comment() {
  local issue_uuid="$1"
  local body="$2"

  linear_graphql \
    'mutation($issueId:String!,$body:String!){
      commentCreate(input:{issueId:$issueId,body:$body}){
        success
      }
    }' \
    "$(jq -cn \
      --arg issueId "$issue_uuid" \
      --arg body "$body" \
      '{issueId:$issueId,body:$body}')"
}

cmd_finish() {
  local issue="${1:-}"
  [[ -n "$issue" ]] || die "usage: $0 finish DHA-15"

  local issue_json
  issue_json="$(fetch_issue "$issue")"

  local identifier
  local title
  local issue_uuid

  identifier="$(jq -r '.issue.identifier // empty' <<<"$issue_json")"
  title="$(jq -r '.issue.title // empty' <<<"$issue_json")"
  issue_uuid="$(jq -r '.issue.id // empty' <<<"$issue_json")"

  [[ -n "$identifier" ]] || die "issue not found: $issue"

  local worktree
  worktree="$(find_issue_worktree "$identifier")"
  [[ -n "$worktree" && -d "$worktree" ]] ||
    die "could not find worktree for $identifier"

  cd "$worktree"

  echo "=== $identifier — $title ==="
  echo

  echo "=== git status ==="
  git status --short
  echo

  echo "=== diff stat ==="
  git diff --stat
  echo

  echo "=== changed files ==="
  git diff --name-only
  echo

  if [[ -z "$(git status --porcelain)" ]]; then
    die "working tree is clean; there is nothing to finish"
  fi

  if [[ -n "${CHECK_CMD:-}" ]]; then
    echo "=== running CHECK_CMD ==="
    echo "$CHECK_CMD"
    bash -lc "$CHECK_CMD"
    echo
  else
    echo "CHECK_CMD is not set; no automatic test command will be guessed."
    echo
  fi

  read -r -p "Review the diff now. Commit this issue? [y/N] " answer
  [[ "$answer" =~ ^[Yy]$ ]] || {
    echo "Stopped before commit."
    exit 0
  }

  git add -A

  echo
  echo "=== staged diff stat ==="
  git diff --cached --stat
  echo

  echo "=== staged files ==="
  git diff --cached --name-only
  echo

  read -r -p "Staged diff looks correct? [y/N] " answer
  [[ "$answer" =~ ^[Yy]$ ]] || {
    git reset
    echo "Unstaged everything; no commit created."
    exit 0
  }

  local commit_message
  commit_message="feat: ${title}"

  git commit -m "$commit_message"

  local commit_hash
  local summary
  local comment

  commit_hash="$(git rev-parse --short HEAD)"
  summary="$(git show --stat --oneline --format='%h %s' HEAD)"

  comment="$(cat <<EOF
Implemented ${identifier}.

Commit: \`${commit_hash}\`

\`\`\`
${summary}
\`\`\`

Local validation:
${CHECK_CMD:-No CHECK_CMD was configured; review/test results should be added manually if needed.}

No push was performed by the workflow script.
EOF
)"

  add_linear_comment "$issue_uuid" "$comment" >/dev/null
  echo "Added completion comment to Linear."

  read -r -p "Mark $identifier Done in Linear? [y/N] " answer

  if [[ "$answer" =~ ^[Yy]$ ]]; then
    local done_state
    done_state="$(linear_done_state_id "$LINEAR_TEAM_KEY")"
    [[ -n "$done_state" ]] ||
      die "could not find completed state for team $LINEAR_TEAM_KEY"

    mark_issue_done "$issue_uuid" "$done_state" >/dev/null
    echo "$identifier marked Done."
  else
    echo "$identifier left in its current Linear state."
  fi

  echo
  echo "=== final status ==="
  git status --short
  echo
  echo "Commit: $commit_hash"
  echo "No push performed."
}

usage() {
  cat <<EOF
Usage:
  $0 next
  $0 start DHA-15
  $0 finish DHA-15

Environment:
  LINEAR_API_KEY       required
  LINEAR_PROJECT       default: noxyn-solari
  LINEAR_TEAM_KEY      default: DHA
  CODEX_MODEL          optional
  CODEX_EXTRA_ARGS     optional
  CHECK_CMD            optional validation command used by finish

Examples:
  export LINEAR_API_KEY='lin_api_...'

  $0 next

  $0 start DHA-15

  CODEX_MODEL='your-model-name' \
    $0 start DHA-15

  CHECK_CMD='pnpm test -- capability-matrix' \
    $0 finish DHA-15
EOF
}

case "${1:-}" in
  next)
    cmd_next
    ;;

  start)
    cmd_start "${2:-}"
    ;;

  finish)
    cmd_finish "${2:-}"
    ;;

  -h|--help|help|"")
    usage
    ;;

  *)
    die "unknown command: $1 (try --help)"
    ;;
esac
