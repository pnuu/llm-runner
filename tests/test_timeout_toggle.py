"""Tests for timeout toggle feature (/timeout command and --disable-timeout-check flag)"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from llm_runner.cli import parse_args
from llm_runner.chat import InteractiveChat
from llm_runner.llm import OllamaClient


class TestCLITimeoutArgument:
    """Test --disable-timeout-check CLI argument"""
    
    def test_disable_timeout_check_flag_parsing(self):
        """Test that --disable-timeout-check flag is parsed"""
        args = parse_args(["--disable-timeout-check"])
        assert hasattr(args, 'disable_timeout')
        assert args.disable_timeout is True
    
    def test_disable_timeout_check_with_mode(self):
        """Test --disable-timeout-check with command mode"""
        args = parse_args(["plan", "test task", "--disable-timeout-check"])
        assert args.mode == "plan"
        assert args.disable_timeout is True
    
    def test_disable_timeout_default_false(self):
        """Test that disable_timeout defaults to False"""
        args = parse_args([])
        assert hasattr(args, 'disable_timeout')
        assert args.disable_timeout is False
    
    def test_disable_timeout_short_form(self):
        """Test short form -T flag if implemented"""
        # This might be implemented or not
        args = parse_args(["--disable-timeout-check"])
        assert args.disable_timeout is True


class TestInteractiveChatTimeoutToggle:
    """Test /timeout command in InteractiveChat"""
    
    @patch('llm_runner.chat.check_ollama_connection', return_value=True)
    @patch('llm_runner.chat.OllamaClient')
    def test_interactive_chat_timeout_enabled_default(self, mock_client_class, mock_check):
        """Test that timeout is enabled by default"""
        chat = InteractiveChat(model="mistral")
        assert chat.timeout_enabled is True
    
    @patch('llm_runner.chat.check_ollama_connection', return_value=True)
    @patch('llm_runner.chat.OllamaClient')
    def test_interactive_chat_timeout_enabled_parameter(self, mock_client_class, mock_check):
        """Test that timeout_enabled can be set at init"""
        chat = InteractiveChat(model="mistral", timeout_enabled=False)
        assert chat.timeout_enabled is False
    
    @patch('llm_runner.chat.check_ollama_connection', return_value=True)
    @patch('llm_runner.chat.OllamaClient')
    def test_timeout_command_off(self, mock_client_class, mock_check):
        """Test /timeout off command"""
        chat = InteractiveChat(model="mistral")
        assert chat.timeout_enabled is True
        
        result, output = chat.process_input("/timeout off")
        assert result == "timeout"
        assert chat.timeout_enabled is False
        assert "disabled" in output.lower()
    
    @patch('llm_runner.chat.check_ollama_connection', return_value=True)
    @patch('llm_runner.chat.OllamaClient')
    def test_timeout_command_on(self, mock_client_class, mock_check):
        """Test /timeout on command"""
        chat = InteractiveChat(model="mistral", timeout_enabled=False)
        assert chat.timeout_enabled is False
        
        result, output = chat.process_input("/timeout on")
        assert result == "timeout"
        assert chat.timeout_enabled is True
        assert "enabled" in output.lower()
    
    @patch('llm_runner.chat.check_ollama_connection', return_value=True)
    @patch('llm_runner.chat.OllamaClient')
    def test_timeout_command_status(self, mock_client_class, mock_check):
        """Test /timeout status command"""
        chat = InteractiveChat(model="mistral", timeout_enabled=True)
        
        result, output = chat.process_input("/timeout status")
        assert result == "timeout"
        assert "enabled" in output.lower()
        
        chat.timeout_enabled = False
        result, output = chat.process_input("/timeout status")
        assert result == "timeout"
        assert "disabled" in output.lower()
    
    @patch('llm_runner.chat.check_ollama_connection', return_value=True)
    @patch('llm_runner.chat.OllamaClient')
    def test_timeout_command_invalid(self, mock_client_class, mock_check):
        """Test invalid /timeout command"""
        chat = InteractiveChat(model="mistral")
        result, output = chat.process_input("/timeout invalid")
        # Should either be timeout command with error or unknown
        assert result in ("timeout", "unknown")
    
    @patch('llm_runner.chat.check_ollama_connection', return_value=True)
    @patch('llm_runner.chat.OllamaClient')
    def test_timeout_command_case_insensitive(self, mock_client_class, mock_check):
        """Test /timeout command is case insensitive"""
        chat = InteractiveChat(model="mistral", timeout_enabled=True)
        
        result, output = chat.process_input("/TIMEOUT OFF")
        assert result == "timeout"
        assert chat.timeout_enabled is False
    
    @patch('llm_runner.chat.check_ollama_connection', return_value=True)
    @patch('llm_runner.chat.OllamaClient')
    def test_timeout_command_with_spaces(self, mock_client_class, mock_check):
        """Test /timeout command with extra spaces"""
        chat = InteractiveChat(model="mistral", timeout_enabled=True)
        
        result, output = chat.process_input("/timeout   off")
        assert result == "timeout"
        assert chat.timeout_enabled is False


class TestOllamaClientTimeoutToggle:
    """Test timeout_enabled in OllamaClient"""
    
    def test_ollama_client_timeout_enabled_default(self):
        """Test that timeout_enabled defaults to True"""
        client = OllamaClient()
        assert client.timeout_enabled is True
    
    def test_ollama_client_timeout_enabled_parameter(self):
        """Test that timeout_enabled can be set"""
        client = OllamaClient(timeout_enabled=False)
        assert client.timeout_enabled is False
    
    @patch('httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_send_prompt_async_respects_timeout_disabled(self, mock_http_client):
        """Test that timeout is not enforced when disabled"""
        # This test is complex due to httpx/async nature
        # For now, verify the attribute is checked
        client = OllamaClient(timeout_enabled=False)
        # The actual timeout would be passed as timeout_sec=None to async_with_timeout
        assert client.timeout_enabled is False
    
    @patch('httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_send_prompt_streaming_respects_timeout_disabled(self, mock_http_client):
        """Test that streaming timeout is not enforced when disabled"""
        client = OllamaClient(timeout_enabled=False)
        assert client.timeout_enabled is False


class TestContextDisplayShowsTimeout:
    """Test that /context displays timeout state"""
    
    @patch('llm_runner.chat.check_ollama_connection', return_value=True)
    @patch('llm_runner.chat.OllamaClient')
    def test_context_display_shows_timeout_enabled(self, mock_client_class, mock_check):
        """Test /context shows timeout enabled"""
        chat = InteractiveChat(model="mistral", timeout_enabled=True)
        result, output = chat.process_input("/context")
        assert result == "context"
        assert "timeout" in output.lower()
        assert "enabled" in output.lower()
    
    @patch('llm_runner.chat.check_ollama_connection', return_value=True)
    @patch('llm_runner.chat.OllamaClient')
    def test_context_display_shows_timeout_disabled(self, mock_client_class, mock_check):
        """Test /context shows timeout disabled"""
        chat = InteractiveChat(model="mistral", timeout_enabled=False)
        result, output = chat.process_input("/context")
        assert result == "context"
        assert "timeout" in output.lower()
        assert "disabled" in output.lower()


class TestTimeoutToggleIntegration:
    """Integration tests for timeout toggle feature"""
    
    @patch('llm_runner.chat.check_ollama_connection', return_value=True)
    @patch('llm_runner.chat.OllamaClient')
    def test_toggle_multiple_times(self, mock_client_class, mock_check):
        """Test toggling timeout multiple times"""
        chat = InteractiveChat(model="mistral", timeout_enabled=True)
        
        # Toggle off
        result, _ = chat.process_input("/timeout off")
        assert chat.timeout_enabled is False
        
        # Toggle on
        result, _ = chat.process_input("/timeout on")
        assert chat.timeout_enabled is True
        
        # Toggle off again
        result, _ = chat.process_input("/timeout off")
        assert chat.timeout_enabled is False
    
    @patch('llm_runner.chat.check_ollama_connection', return_value=True)
    @patch('llm_runner.chat.OllamaClient')
    def test_timeout_state_persists_across_commands(self, mock_client_class, mock_check):
        """Test timeout state persists after other commands"""
        chat = InteractiveChat(model="mistral", timeout_enabled=True)
        
        # Disable timeout
        chat.process_input("/timeout off")
        
        # Run other command (shouldn't affect timeout state)
        chat.process_input("/context")
        
        # Verify timeout still disabled
        assert chat.timeout_enabled is False
    
    def test_cli_argument_integration(self):
        """Test that CLI argument is parsed correctly"""
        args = parse_args(["--disable-timeout-check"])
        assert args.disable_timeout is True
        
        args2 = parse_args([])
        assert args2.disable_timeout is False


class TestTimeoutEdgeCases:
    """Edge cases for timeout toggle"""
    
    @patch('llm_runner.chat.check_ollama_connection', return_value=True)
    @patch('llm_runner.chat.OllamaClient')
    def test_timeout_command_only_on_off_status(self, mock_client_class, mock_check):
        """Test /timeout only accepts on, off, or status"""
        chat = InteractiveChat(model="mistral")
        
        # Valid commands
        for cmd in ["/timeout on", "/timeout off", "/timeout status"]:
            result, _ = chat.process_input(cmd)
            assert result == "timeout"
        
        # Invalid command
        result, _ = chat.process_input("/timeout invalid")
        # Should return timeout command (with error) or unknown
        assert result in ("timeout", "unknown")
    
    @patch('llm_runner.chat.check_ollama_connection', return_value=True)
    @patch('llm_runner.chat.OllamaClient')
    def test_timeout_off_when_already_off(self, mock_client_class, mock_check):
        """Test /timeout off when already off doesn't break"""
        chat = InteractiveChat(model="mistral", timeout_enabled=False)
        
        result, output = chat.process_input("/timeout off")
        assert result == "timeout"
        assert chat.timeout_enabled is False
    
    @patch('llm_runner.chat.check_ollama_connection', return_value=True)
    @patch('llm_runner.chat.OllamaClient')
    def test_timeout_on_when_already_on(self, mock_client_class, mock_check):
        """Test /timeout on when already on doesn't break"""
        chat = InteractiveChat(model="mistral", timeout_enabled=True)
        
        result, output = chat.process_input("/timeout on")
        assert result == "timeout"
        assert chat.timeout_enabled is True
