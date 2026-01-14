from mcp.server.fastmcp import FastMCP
import subprocess
import json
import os
import tempfile
from pathlib import Path

# Create the FastMCP server instance
mcp = FastMCP("mcp-documentation-server")

# Register the tool using FastMCP decorator
@mcp.tool()
def scan_docker_with_prisma(docker_id) -> dict:
    """
    This server will in-take docker id and scan the container for vulnerabilities.
    It will return a JSON object with the scan results.
    It will scan using Twistlock/Prisma cli tool
    """
    TWISTCLI_EXECUTABLE = os.environ.get("TWISTCLI_EXECUTABLE", " ")
    TWISTLOCK_API_URL = os.environ.get("TWISTLOCK_API_URL", " ")
    api_token = os.environ.get("TWISTLOCK_API_TOKEN", " ")

    # write twistcli results to a temp file
    with tempfile.NamedTemporaryFile(prefix="twistcli_scan_", suffix=".json", delete=False) as tf:
        output_path = Path(tf.name)

    command = [
        "twistcli",
        "images",
        "scan",
        "--address",
        TWISTLOCK_API_URL,
        "--token",
        api_token,
        "--details",
        "--output-file",
        str(output_path),
        docker_id,
    ]
    try:
        # 3. Run the command
        result = subprocess.run(command, check=True, capture_output=True, text=True)

        # 4. Read and parse the JSON output file written by twistcli
        try:
            with output_path.open("r", encoding="utf-8") as fh:
                scan_results = json.load(fh)
        finally:
            # Clean up temporary file
            try:
                output_path.unlink()
            except Exception:
                pass

        return scan_results

    except FileNotFoundError:
        print(f"Error: The command '{TWISTCLI_EXECUTABLE}' was not found.")
        print("Please ensure 'twistcli.exe' exists at that path or set TWISTCLI_EXECUTABLE environment variable.")
        return None
    except subprocess.CalledProcessError as e:
        # This block runs if the command returns a non-zero exit code (an error)
        print("Error: The twistcli command failed.")
        print(f"Return Code: {e.returncode}")
        print(f"Error Output:\n{e.stderr}")
        # Attempt to show content of output file if present
        if output_path.exists():
            try:
                with output_path.open("r", encoding="utf-8") as fh:
                    print("twistcli output file contents:")
                    print(fh.read())
            except Exception:
                pass
        return None


if __name__ == "__main__":
    mcp.run("stdio")
    
