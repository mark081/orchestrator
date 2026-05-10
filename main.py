import sys
from dotenv import load_dotenv
import anthropic
from orchestrator import run_pipeline


def main() -> None:
    load_dotenv()
    topic = sys.argv[1] if len(sys.argv) > 1 else input("Enter topic: ").strip()
    if not topic:
        print("Error: topic cannot be empty.")
        sys.exit(1)

    try:
        client = anthropic.Anthropic()
    except Exception as e:
        print(f"Error creating Anthropic client: {e}")
        print("Make sure ANTHROPIC_API_KEY is set in your environment or .env file.")
        sys.exit(1)

    final_report = run_pipeline(client, topic)

    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(final_report)


if __name__ == "__main__":
    main()
