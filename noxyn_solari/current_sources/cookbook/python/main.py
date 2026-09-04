from solari_sandbox import SandboxClient


async def create_sandbox(client: SandboxClient) -> None:
    await client.create(template="base", mem_mb=2048)
