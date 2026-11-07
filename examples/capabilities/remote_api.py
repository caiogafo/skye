"""Remote HTTP APIs as capabilities.

``RemoteAPICapability`` wraps an HTTP endpoint: the model's arguments become the query string (GET) or the JSON body (POST, PUT, PATCH,
DELETE). Headers, basic authentication and a timeout are options of the capability. This example builds the configurations, runs one call
against a public API when the network is reachable, and prints a note when it is not. With OPENAI_API_KEY set the model is real, otherwise
a scripted client asks for the call.
"""

import asyncio
import sys
from pathlib import Path

from skye import UserMessage
from skye.tools import CapabilitySchema, RemoteAPICapability

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the shared offline helper lives in examples/
from _offline import get_client  # noqa: E402

posts = RemoteAPICapability(
    name="posts.get_user_posts",
    description="Get posts by a user from JSONPlaceholder",
    url="https://jsonplaceholder.typicode.com/posts",
    method="GET",
    schema=CapabilitySchema(
        name="posts.get_user_posts",
        description="Get posts by a user from JSONPlaceholder",
        parameters={"type": "object", "properties": {"userId": {"type": "integer"}}, "required": ["userId"]},
    ),
    timeout=10.0,
)

# Other configurations: headers, basic authentication, other methods, a timeout
repos = RemoteAPICapability("github.search", "Search repositories", "https://api.github.com/search/repositories", method="GET",
                            headers={"Accept": "application/vnd.github+json"})
private = RemoteAPICapability("crm.create", "Create a record", "https://api.example.com/records", method="POST", auth=("user", "secret"))


async def main() -> None:
    for cap in (posts, repos, private):
        print("configured:", cap.get_schema().name)

    client = get_client("openai")
    response = client.complete(messages=[UserMessage(content="Get the posts of user 2")], model="gpt-4", capabilities=[posts])
    if not response.has_capability_calls():
        print(response.content)
        return
    try:
        for message in await response.aexecute_capability_calls():
            print(f"{message.capability_name}: {message.content[:100]}")
    except OSError as error:
        print(f"the API is not reachable from here ({error}); the call and its arguments are shown above")
    print("the model asked for:", [(c.name, c.arguments) for c in response.capability_calls])


if __name__ == "__main__":
    asyncio.run(main())
