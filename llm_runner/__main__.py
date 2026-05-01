"""Entry point for llm-runner CLI"""
import sys
from llm_runner.cli import run_cli


def main():
    """Main entry point"""
    run_cli(sys.argv[1:])


if __name__ == "__main__":
    main()
