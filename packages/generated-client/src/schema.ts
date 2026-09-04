export interface paths {
  "/health": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Get Health
     * @description Report readiness only after PostgreSQL responds.
     */
    get: operations["getHealth"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/v1/executions/{execution_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Get Execution */
    get: operations["getExecution"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/v1/findings/{finding_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Get Finding */
    get: operations["getFinding"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/v1/findings/{finding_id}/proposals": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Create Proposal */
    post: operations["createFindingProposal"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/v1/me": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Get Me */
    get: operations["getCurrentWorkspace"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/v1/onboarding": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    /** Update Draft */
    patch: operations["updateOnboardingDraft"];
    trace?: never;
  };
  "/v1/products/{product_id}/configuration": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Get Configuration */
    get: operations["getProductConfiguration"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/v1/products/{product_id}/configurations": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Create Configuration */
    post: operations["createProductConfiguration"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/v1/products/{product_id}/runs": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** List Runs */
    get: operations["listVerificationRuns"];
    put?: never;
    /** Start Run */
    post: operations["startVerificationRun"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/v1/projects": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Create Project */
    post: operations["createProject"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/v1/projects/{project_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Get Project */
    get: operations["getProject"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/v1/projects/{project_id}/products": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Create Product */
    post: operations["createProduct"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/v1/proposals/{proposal_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Get Proposal */
    get: operations["getProposal"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/v1/proposals/{proposal_id}/verify": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Verify Proposal */
    post: operations["verifyProposal"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/v1/runs/{run_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Get Run */
    get: operations["getVerificationRun"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/v1/runs/{run_id}/cancel": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Cancel Run */
    post: operations["cancelVerificationRun"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/v1/runs/{run_id}/executions": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** List Executions */
    get: operations["listRunExecutions"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/v1/runs/{run_id}/findings": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** List Findings */
    get: operations["listRunFindings"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/v1/runs/{run_id}/matrix": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Get Matrix */
    get: operations["getVerificationMatrix"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/v1/runs/{run_id}/proposals": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** List Proposals */
    get: operations["listRunProposals"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
}
export type webhooks = Record<string, never>;
export interface components {
  schemas: {
    /** ArtifactView */
    ArtifactView: {
      /** Byte Length */
      byte_length: number;
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Kind */
      kind: string;
      /** Sha256 */
      sha256: string;
    };
    /** ConfigurationCreate */
    ConfigurationCreate: {
      /** Packages */
      packages: components["schemas"]["PackageSpec"][];
      /** Sources */
      sources: string[];
    };
    /** ConfigurationView */
    ConfigurationView: {
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Packages */
      packages: components["schemas"]["PackageSpec"][];
      /**
       * Product Id
       * Format: uuid
       */
      product_id: string;
      /** Sources */
      sources: string[];
      /**
       * Version
       * @constant
       */
      version: 1;
    };
    /** ContractDiffView */
    ContractDiffView: {
      /** After */
      after: string;
      /** Before */
      before: string;
      /** Capabilityid */
      capabilityId: string;
      /**
       * Classification
       * @constant
       */
      classification: "RENAMED";
    };
    /** DraftUpdate */
    DraftUpdate: {
      /**
       * Current Step
       * @enum {string}
       */
      current_step: "project" | "product" | "configuration";
      /** Project Name */
      project_name?: string | null;
      /** Project Slug */
      project_slug?: string | null;
    };
    /** DraftView */
    DraftView: {
      /**
       * Current Step
       * @enum {string}
       */
      current_step: "project" | "product" | "configuration" | "complete";
      /** Product Id */
      product_id?: string | null;
      /** Project Id */
      project_id?: string | null;
      /** Project Name */
      project_name?: string | null;
      /** Project Slug */
      project_slug?: string | null;
    };
    /** ExecutionList */
    ExecutionList: {
      /** Items */
      items: components["schemas"]["ExecutionView"][];
    };
    /** ExecutionView */
    ExecutionView: {
      /** Attempt Number */
      attempt_number: number;
      /**
       * Backend
       * @enum {string}
       */
      backend: "REPLAY" | "SOLARI";
      /** Cancelled */
      cancelled: boolean;
      /**
       * Cleanup State
       * @enum {string}
       */
      cleanup_state: "PASS" | "FAIL" | "NOT_REQUIRED";
      /** Command Sha256 */
      command_sha256: string;
      /**
       * Completed At
       * Format: date-time
       */
      completed_at: string;
      /** Duration Ms */
      duration_ms: number;
      /** Error Code */
      error_code: string | null;
      evidence: components["schemas"]["ArtifactView"];
      /** Exit Code */
      exit_code: number | null;
      /** Finding Id */
      finding_id: string | null;
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Infrastructure State
       * @enum {string}
       */
      infrastructure_state: "PASS" | "FAIL";
      /** Infrastructure Step */
      infrastructure_step: string;
      /**
       * Language
       * @enum {string}
       */
      language: "python" | "typescript" | "go";
      /** Output Truncated */
      output_truncated: boolean;
      /** Package Name */
      package_name: string;
      /** Package Version */
      package_version: string;
      /**
       * Phase
       * @enum {string}
       */
      phase: "VERIFY" | "FIX_VERIFY";
      /** Proposal Id */
      proposal_id: string | null;
      /**
       * Run Id
       * Format: uuid
       */
      run_id: string;
      /** Sandbox Id */
      sandbox_id: string | null;
      /** Source Path */
      source_path: string;
      /** Source Sha256 */
      source_sha256: string;
      /** Source Surface */
      source_surface: string;
      /**
       * Started At
       * Format: date-time
       */
      started_at: string;
      /** Stderr */
      stderr: string;
      /** Stdout */
      stdout: string;
      /**
       * Subject State
       * @enum {string}
       */
      subject_state: "PASS" | "FAIL" | "NOT_RUN";
    };
    /** FindingEvidenceView */
    FindingEvidenceView: {
      /**
       * Artifact Id
       * Format: uuid
       */
      artifact_id: string;
      /** Excerpt */
      excerpt: string;
      /** Locator */
      locator: string;
      /** Path */
      path: string;
      /** Sha256 */
      sha256: string;
    };
    /** FindingList */
    FindingList: {
      /** Items */
      items: components["schemas"]["FindingView"][];
    };
    /** FindingView */
    FindingView: {
      /** Capability Id */
      capability_id: string;
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
      evidence: components["schemas"]["FindingEvidenceView"];
      /** Expected Value */
      expected_value: string;
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Lifecycle State
       * @enum {string}
       */
      lifecycle_state:
        | "SUSPECTED"
        | "REPRODUCED"
        | "FIX_PROPOSED"
        | "FIX_VERIFIED"
        | "DISMISSED"
        | "UNVERIFIED";
      /** Observed Value */
      observed_value: string | null;
      /**
       * Run Id
       * Format: uuid
       */
      run_id: string;
      /** Source Surface */
      source_surface: string;
      /**
       * Static State
       * @constant
       */
      static_state: "SUSPECTED";
      /** Summary */
      summary: string;
    };
    /** HTTPValidationError */
    HTTPValidationError: {
      /** Detail */
      detail?: components["schemas"]["ValidationError"][];
    };
    /**
     * HealthResponse
     * @description Readiness information safe to expose without authentication.
     */
    HealthResponse: {
      /**
       * Database
       * @default connected
       * @constant
       */
      database: "connected";
      /**
       * Service
       * @default noxyn-api
       * @constant
       */
      service: "noxyn-api";
      /**
       * Status
       * @default ok
       * @constant
       */
      status: "ok";
      /** Version */
      version: string;
    };
    /** MatrixCellView */
    MatrixCellView: {
      evidence: components["schemas"]["MatrixEvidenceView"] | null;
      /** Expected */
      expected: string;
      /** Findingid */
      findingId?: string | null;
      /** Observed */
      observed: string | null;
      /**
       * State
       * @enum {string}
       */
      state: "ALIGNED" | "SUSPECTED" | "NOT_EXPECTED" | "UNVERIFIED";
      /** Summary */
      summary: string;
      /** Surface */
      surface: string;
    };
    /** MatrixEvidenceView */
    MatrixEvidenceView: {
      /** Excerpt */
      excerpt: string;
      /** Locator */
      locator: string;
      /** Path */
      path: string;
      /** Sha256 */
      sha256: string;
    };
    /** MatrixRowView */
    MatrixRowView: {
      /** Capabilityid */
      capabilityId: string;
      /** Cells */
      cells: components["schemas"]["MatrixCellView"][];
      /** Label */
      label: string;
      runtime: components["schemas"]["RuntimeCellView"];
      /** Runtimecells */
      runtimeCells?: components["schemas"]["RuntimeCellView"][];
    };
    /** MatrixSummaryView */
    MatrixSummaryView: {
      /** Aligned */
      aligned: number;
      /** Capabilities */
      capabilities: number;
      /** Notexpected */
      notExpected: number;
      /** Suspected */
      suspected: number;
      /** Unverified */
      unverified: number;
    };
    /** MatrixView */
    MatrixView: {
      contractDiff: components["schemas"]["ContractDiffView"];
      /**
       * Fixture
       * @constant
       */
      fixture: true;
      /** Manifestsha256 */
      manifestSha256: string;
      /** Packages */
      packages: {
        [key: string]: components["schemas"]["PackageIdentityView"];
      };
      parity?: components["schemas"]["ParityView"] | null;
      /** Parserversion */
      parserVersion: string;
      /** Rows */
      rows: components["schemas"]["MatrixRowView"][];
      /**
       * Scenario
       * @constant
       */
      scenario: "sandbox-create-evolution";
      /**
       * Schemaversion
       * @constant
       */
      schemaVersion: "noxyn-static-analysis-result/1.0";
      summary: components["schemas"]["MatrixSummaryView"];
    };
    /** MeResponse */
    MeResponse: {
      onboarding: components["schemas"]["DraftView"];
      /** Project Id */
      project_id?: string | null;
      workspace: components["schemas"]["WorkspaceView"];
    };
    /** PackageIdentityView */
    PackageIdentityView: {
      /** Import */
      import: string;
      /** Name */
      name: string;
      /** Version */
      version: string;
    };
    /** PackageSpec */
    PackageSpec: {
      /**
       * Ecosystem
       * @enum {string}
       */
      ecosystem: "python" | "typescript" | "go";
      /** Package */
      package: string;
      /** Version */
      version: string;
    };
    /** ParityView */
    ParityView: {
      /** Comparedlanguages */
      comparedLanguages: ("python" | "typescript" | "go")[];
      /**
       * State
       * @enum {string}
       */
      state: "MATCH" | "DIFFERENT" | "INCOMPLETE";
      /** Summary */
      summary: string;
    };
    /** ProductCreate */
    ProductCreate: {
      /**
       * Slug
       * @default sandbox
       * @constant
       */
      slug: "sandbox";
    };
    /** ProductView */
    ProductView: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Name */
      name: string;
      /**
       * Project Id
       * Format: uuid
       */
      project_id: string;
      /**
       * Slug
       * @constant
       */
      slug: "sandbox";
    };
    /** ProjectCreate */
    ProjectCreate: {
      /** Name */
      name: string;
      /** Slug */
      slug: string;
    };
    /** ProjectView */
    ProjectView: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Name */
      name: string;
      /** Slug */
      slug: string;
    };
    /** ProposalList */
    ProposalList: {
      /** Items */
      items: components["schemas"]["ProposalView"][];
    };
    /** ProposalView */
    ProposalView: {
      /** Changed Lines */
      changed_lines: number;
      /**
       * Checkout Modified
       * @default false
       * @constant
       */
      checkout_modified: false;
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
      /**
       * Finding Id
       * Format: uuid
       */
      finding_id: string;
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Patch */
      patch: string;
      patch_artifact: components["schemas"]["ArtifactView"];
      proposed_artifact: components["schemas"]["ArtifactView"];
      /** Proposed Sha256 */
      proposed_sha256: string;
      /**
       * Run Id
       * Format: uuid
       */
      run_id: string;
      source_artifact: components["schemas"]["ArtifactView"];
      /** Source Path */
      source_path: string;
      /** Source Sha256 */
      source_sha256: string;
      /**
       * Source Surface
       * @enum {string}
       */
      source_surface: "python" | "docs_python";
      /**
       * State
       * @enum {string}
       */
      state: "FIX_PROPOSED" | "FIX_VERIFIED" | "DISMISSED";
      verification: components["schemas"]["ExecutionView"] | null;
      /** Verification Job State */
      verification_job_state:
        | ("QUEUED" | "LEASED" | "COMPLETED" | "FAILED" | "CANCELLED")
        | null;
      /** Verified At */
      verified_at: string | null;
    };
    /** RunCreate */
    RunCreate: {
      /**
       * Scenario
       * @default controlled_api_evolution
       * @constant
       */
      scenario: "controlled_api_evolution";
    };
    /** RunList */
    RunList: {
      /** Items */
      items: components["schemas"]["RunView"][];
    };
    /** RunView */
    RunView: {
      artifact?: components["schemas"]["ArtifactView"] | null;
      /** Attempt */
      attempt: number;
      /** Cancel Requested At */
      cancel_requested_at?: string | null;
      /** Completed At */
      completed_at?: string | null;
      /**
       * Configuration Id
       * Format: uuid
       */
      configuration_id: string;
      /** Configuration Version */
      configuration_version: number;
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
      /** Error Code */
      error_code?: string | null;
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Max Attempts */
      max_attempts: number;
      /**
       * Product Id
       * Format: uuid
       */
      product_id: string;
      /** Scenario */
      scenario: string;
      /** Started At */
      started_at?: string | null;
      /**
       * State
       * @enum {string}
       */
      state:
        | "QUEUED"
        | "SNAPSHOTTING"
        | "ANALYZING"
        | "VERIFYING"
        | "PROPOSING"
        | "REVERIFYING"
        | "CANCEL_REQUESTED"
        | "COMPLETED"
        | "FAILED"
        | "CANCELLED";
    };
    /** RuntimeCellView */
    RuntimeCellView: {
      /** Backend */
      backend?: ("REPLAY" | "SOLARI") | null;
      /** Executionid */
      executionId?: string | null;
      /** Infrastructurestate */
      infrastructureState?: ("PASS" | "FAIL") | null;
      /**
       * Language
       * @default python
       * @enum {string}
       */
      language: "python" | "typescript" | "go";
      /**
       * Sourcesurface
       * @default python
       */
      sourceSurface: string;
      /**
       * State
       * @enum {string}
       */
      state: "NOT_RUN" | "PASS" | "FAIL" | "UNVERIFIED";
      /** Subjectstate */
      subjectState?: ("PASS" | "FAIL" | "NOT_RUN") | null;
      /** Summary */
      summary: string;
    };
    /** ValidationError */
    ValidationError: {
      /** Context */
      ctx?: Record<string, never>;
      /** Input */
      input?: unknown;
      /** Location */
      loc: (string | number)[];
      /** Message */
      msg: string;
      /** Error Type */
      type: string;
    };
    /** WorkspaceView */
    WorkspaceView: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Name */
      name: string;
      /** Onboarding Complete */
      onboarding_complete: boolean;
    };
  };
  responses: never;
  parameters: never;
  requestBodies: never;
  headers: never;
  pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
  getHealth: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HealthResponse"];
        };
      };
    };
  };
  getExecution: {
    parameters: {
      query?: never;
      header?: {
        authorization?: string | null;
        "X-Noxyn-Test-User"?: string | null;
      };
      path: {
        execution_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ExecutionView"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  getFinding: {
    parameters: {
      query?: never;
      header?: {
        authorization?: string | null;
        "X-Noxyn-Test-User"?: string | null;
      };
      path: {
        finding_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["FindingView"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  createFindingProposal: {
    parameters: {
      query?: never;
      header?: {
        "Idempotency-Key"?: string | null;
        "X-CSRF-Token"?: string | null;
        authorization?: string | null;
        "X-Noxyn-Test-User"?: string | null;
      };
      path: {
        finding_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ProposalView"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  getCurrentWorkspace: {
    parameters: {
      query?: never;
      header?: {
        authorization?: string | null;
        "X-Noxyn-Test-User"?: string | null;
      };
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["MeResponse"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  updateOnboardingDraft: {
    parameters: {
      query?: never;
      header?: {
        "Idempotency-Key"?: string | null;
        authorization?: string | null;
        "X-Noxyn-Test-User"?: string | null;
      };
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["DraftUpdate"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["DraftView"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  getProductConfiguration: {
    parameters: {
      query?: never;
      header?: {
        authorization?: string | null;
        "X-Noxyn-Test-User"?: string | null;
      };
      path: {
        product_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ConfigurationView"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  createProductConfiguration: {
    parameters: {
      query?: never;
      header?: {
        "Idempotency-Key"?: string | null;
        authorization?: string | null;
        "X-Noxyn-Test-User"?: string | null;
      };
      path: {
        product_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["ConfigurationCreate"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ConfigurationView"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  listVerificationRuns: {
    parameters: {
      query?: {
        limit?: number;
      };
      header?: {
        authorization?: string | null;
        "X-Noxyn-Test-User"?: string | null;
      };
      path: {
        product_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["RunList"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  startVerificationRun: {
    parameters: {
      query?: never;
      header?: {
        "Idempotency-Key"?: string | null;
        "X-CSRF-Token"?: string | null;
        authorization?: string | null;
        "X-Noxyn-Test-User"?: string | null;
      };
      path: {
        product_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["RunCreate"];
      };
    };
    responses: {
      /** @description Successful Response */
      202: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["RunView"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  createProject: {
    parameters: {
      query?: never;
      header?: {
        "Idempotency-Key"?: string | null;
        authorization?: string | null;
        "X-Noxyn-Test-User"?: string | null;
      };
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["ProjectCreate"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ProjectView"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  getProject: {
    parameters: {
      query?: never;
      header?: {
        authorization?: string | null;
        "X-Noxyn-Test-User"?: string | null;
      };
      path: {
        project_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ProjectView"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  createProduct: {
    parameters: {
      query?: never;
      header?: {
        "Idempotency-Key"?: string | null;
        authorization?: string | null;
        "X-Noxyn-Test-User"?: string | null;
      };
      path: {
        project_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["ProductCreate"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ProductView"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  getProposal: {
    parameters: {
      query?: never;
      header?: {
        authorization?: string | null;
        "X-Noxyn-Test-User"?: string | null;
      };
      path: {
        proposal_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ProposalView"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  verifyProposal: {
    parameters: {
      query?: never;
      header?: {
        "Idempotency-Key"?: string | null;
        "X-CSRF-Token"?: string | null;
        authorization?: string | null;
        "X-Noxyn-Test-User"?: string | null;
      };
      path: {
        proposal_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      202: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ProposalView"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  getVerificationRun: {
    parameters: {
      query?: never;
      header?: {
        authorization?: string | null;
        "X-Noxyn-Test-User"?: string | null;
      };
      path: {
        run_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["RunView"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  cancelVerificationRun: {
    parameters: {
      query?: never;
      header?: {
        "Idempotency-Key"?: string | null;
        "X-CSRF-Token"?: string | null;
        authorization?: string | null;
        "X-Noxyn-Test-User"?: string | null;
      };
      path: {
        run_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["RunView"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  listRunExecutions: {
    parameters: {
      query?: never;
      header?: {
        authorization?: string | null;
        "X-Noxyn-Test-User"?: string | null;
      };
      path: {
        run_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ExecutionList"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  listRunFindings: {
    parameters: {
      query?: never;
      header?: {
        authorization?: string | null;
        "X-Noxyn-Test-User"?: string | null;
      };
      path: {
        run_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["FindingList"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  getVerificationMatrix: {
    parameters: {
      query?: never;
      header?: {
        authorization?: string | null;
        "X-Noxyn-Test-User"?: string | null;
      };
      path: {
        run_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["MatrixView"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  listRunProposals: {
    parameters: {
      query?: never;
      header?: {
        authorization?: string | null;
        "X-Noxyn-Test-User"?: string | null;
      };
      path: {
        run_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ProposalList"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
}
