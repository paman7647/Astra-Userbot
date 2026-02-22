# -----------------------------------------------------------
# Astra-Userbot - Universal Multi-Language Executor
# -----------------------------------------------------------

import asyncio
import shutil
import os
import uuid

from . import *  # Astra helpers (astra_command, extract_args, smart_reply, report_error)

# -----------------------------------------------------------
# LANGUAGE DEFINITIONS + SHELL + POWERSHELL
# -----------------------------------------------------------

LANG_EXECUTORS = {
    # ------------------------ Python ------------------------
    "py": {
        "aliases": ["python", "python3", "py"],
        "binary": "python3",
        "ext": ".py",
        "run_cmd": lambda bin, f: f"{bin} {f}",
    },

    # ------------------------ JavaScript ---------------------
    "js": {
        "aliases": ["javascript", "node", "js"],
        "binary": "node",
        "ext": ".js",
        "run_cmd": lambda bin, f: f"{bin} {f}",
    },

    # ------------------------ Shell (Linux/macOS) ------------
    "sh": {
        "aliases": ["sh", "shell", "bash", "zsh"],
        "binary": "bash",
        "ext": ".sh",
        "run_cmd": lambda bin, f: f"{bin} {f}",
    },

    # ------------------------ PowerShell (Windows) ----------
    "pwsh": {
        "aliases": ["powershell", "pwsh", "ps"],
        "binary": "pwsh",   # pwsh is PowerShell Core (Linux/mac/Win)
        "ext": ".ps1",
        "run_cmd": lambda bin, f: f"{bin} -File {f}",
    },

    # ------------------------ PHP ----------------------------
    "php": {
        "aliases": ["php"],
        "binary": "php",
        "ext": ".php",
        "run_cmd": lambda bin, f: f"{bin} {f}",
    },

    # ------------------------ Ruby ---------------------------
    "ruby": {
        "aliases": ["ruby", "rb"],
        "binary": "ruby",
        "ext": ".rb",
        "run_cmd": lambda bin, f: f"{bin} {f}",
    },

    # ------------------------ Lua ----------------------------
    "lua": {
        "aliases": ["lua"],
        "binary": "lua",
        "ext": ".lua",
        "run_cmd": lambda bin, f: f"{bin} {f}",
    },

    # ------------------------ Perl ---------------------------
    "perl": {
        "aliases": ["perl"],
        "binary": "perl",
        "ext": ".pl",
        "run_cmd": lambda bin, f: f"{bin} {f}",
    },

    # ------------------------ Golang -------------------------
    "go": {
        "aliases": ["go"],
        "binary": "go",
        "ext": ".go",
        "run_cmd": lambda bin, f: f"go run {f}",
    },

    # ------------------------ Rust ---------------------------
    "rust": {
        "aliases": ["rust", "rs", "rustc"],
        "binary": "rustc",
        "ext": ".rs",
        "run_cmd": lambda bin, f: f"rustc {f} -o /tmp/a.out && /tmp/a.out",
    },

    # ------------------------ C ------------------------------
    "c": {
        "aliases": ["c", "gcc"],
        "binary": "gcc",
        "ext": ".c",
        "run_cmd": lambda bin, f: f"gcc {f} -o /tmp/a.out && /tmp/a.out",
    },

    # ------------------------ C++ ----------------------------
    "cpp": {
        "aliases": ["cpp", "g++"],
        "binary": "g++",
        "ext": ".cpp",
        "run_cmd": lambda bin, f: f"g++ {f} -o /tmp/a.out && /tmp/a.out",
    },

    # ------------------------ Java ---------------------------
    "java": {
        "aliases": ["java", "javac"],
        "binary": "javac",
        "ext": ".java",
        "run_cmd": lambda bin, f: (
            f"javac {f} -d /tmp && java -cp /tmp {os.path.basename(f).replace('.java','')}"
        ),
    },
}


def is_installed(binary: str) -> bool:
    """Check if required binary is installed."""
    return shutil.which(binary) is not None


# -----------------------------------------------------------
# UNIVERSAL MULTI-LANGUAGE EXECUTION COMMAND
# -----------------------------------------------------------

@astra_command(
    name="run",
    description="Execute code in any programming language (shell & powershell included)",
    category="System",
    aliases=["exec-lang", "code"],
    usage=".run <lang> <code> (e.g. .run python print(1))",
    owner_only=True,
)
async def multi_lang_exec_handler(client: Client, message: Message):
    """Execute code in the selected programming language."""
    try:
        args = extract_args(message)

        if len(args) < 2:
            return await smart_reply(
                message,
                "⚠️ Usage:\n`.run <language> <code>`\nExample: `.run py print(5)`",
            )

        lang = args[0].lower()
        code = " ".join(args[1:])

        # Identify language
        selected = None
        for key, data in LANG_EXECUTORS.items():
            if lang in data["aliases"]:
                selected = data
                break

        if not selected:
            return await smart_reply(message, f"❌ Unsupported language: `{lang}`")

        binary = selected["binary"]

        # Check install status
        if not is_installed(binary):
            return await smart_reply(message, f"❌ `{binary}` is not installed on this system.")

        # Save code to temp file
        filename = f"/tmp/astra_{uuid.uuid4().hex}{selected['ext']}"
        with open(filename, "w") as f:
            f.write(code)

        # Execute
        run_cmd = selected["run_cmd"](binary, filename)

        process = await asyncio.create_subprocess_shell(
            run_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        output = ""
        if stdout:
            output += f"*Output:*\n```\n{stdout.decode()}\n```\n"
        if stderr:
            output += f"*Error:*\n```\n{stderr.decode()}\n```"

        if not output.strip():
            output = "✅ Executed (no output)."

        await smart_reply(message, output)

        # Cleanup
        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        await smart_reply(message, f"❌ Error: {str(e)}")
        await report_error(client, e, context="multi-lang exec failed")


# -----------------------------------------------------------
# EXAMPLES FOR HELP / README
# -----------------------------------------------------------

EXAMPLES = """
📝 *Code Execution Examples*

🔹 Python:
`.run py print("Hello Python!")`

🔹 JavaScript:
`.run js console.log("Hello JS!")`

🔹 Linux Shell:
`.run sh echo Hello from Bash`

🔹 PowerShell:
`.run pwsh Write-Host "Hello from PowerShell"`

🔹 PHP:
`.run php echo "Hello PHP";`

🔹 C:
`.run c #include<stdio.h>\nint main(){ printf("Hi C"); }`

🔹 Java:
`.run java class A{ public static void main(String[]a){ System.out.println("Hello"); }}`
"""