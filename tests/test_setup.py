"""Test project setup"""

def test_project_imports():
    """Test that main modules can be imported"""
    import llm_runner
    from llm_runner import __version__
    assert __version__ == "0.1.0"
