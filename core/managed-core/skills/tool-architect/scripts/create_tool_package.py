#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Scaffold a /tools package.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--tool-name", required=True)
    parser.add_argument("--summary", required=True)
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    tool_dir = repo / "tools" / args.tool_name
    (tool_dir / "bin").mkdir(parents=True, exist_ok=True)
    (tool_dir / "test").mkdir(parents=True, exist_ok=True)

    readme = tool_dir / "README.md"
    if not readme.exists():
        readme.write_text(
            "# {name}\n\n## Capability Summary\n{summary}\n\n".format(
                name=args.tool_name,
                summary=args.summary,
            )
            + "## CLI\n- --help\n- --version\n- --json\n",
            encoding="utf-8",
        )

    interface = tool_dir / "interface.json"
    if not interface.exists():
        payload = {
            "name": args.tool_name,
            "description": args.summary,
            "capability_summary": args.summary,
            "parameters": [
                {"name": "input", "type": "string", "description": "Primary input."}
            ],
        }
        interface.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    wrapper = tool_dir / "bin" / f"{args.tool_name}.py"
    if not wrapper.exists():
        wrapper.write_text(
            "#!/usr/bin/env python3\nimport json\nimport argparse\n\n"
            "def main():\n"
            "    p=argparse.ArgumentParser()\n"
            "    p.add_argument('--version', action='store_true')\n"
            "    p.add_argument('--json', action='store_true')\n"
            "    p.add_argument('input', nargs='?')\n"
            "    a=p.parse_args()\n"
            "    if a.version:\n"
            "        print('1.0.0')\n"
            "        return\n"
            "    data={'status':'ok','input':a.input}\n"
            "    print(json.dumps(data) if a.json else str(data))\n"
            "\nif __name__=='__main__':\n    main()\n",
            encoding="utf-8",
        )
        wrapper.chmod(0o755)

    test_file = tool_dir / "test" / "smoke.sh"
    if not test_file.exists():
        test_file.write_text(
            "#!/usr/bin/env bash\nset -euo pipefail\n"
            f"python3 ../bin/{args.tool_name}.py --version >/dev/null\n"
            f"python3 ../bin/{args.tool_name}.py --json hello >/dev/null\n",
            encoding="utf-8",
        )
        test_file.chmod(0o755)

    print(json.dumps({"status": "success", "tool": args.tool_name, "path": str(tool_dir)}, indent=2))


if __name__ == "__main__":
    main()
