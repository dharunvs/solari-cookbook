# Controlled Python quickstart fixture

This snippet intentionally represents documentation written for fixture v1.

```python
from __future__ import annotations

import asyncio
import os

from solari_sandbox import SandboxClient


async def main() -> None:
    async with SandboxClient(
        api_key=os.environ["SOLARI_API_KEY"],
        base_url=os.getenv("SOLARI_API_BASE_URL", "https://api.getsolari.com"),
    ) as client:
        subject = None
        try:
            # Intentionally stale: solari-sandbox 0.2.0 expects mem_mb.
            subject = await client.create(template="base", memory=2048)
        finally:
            if subject is not None:
                await subject.kill()


if __name__ == "__main__":
    asyncio.run(main())
```
