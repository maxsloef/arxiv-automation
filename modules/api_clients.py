class APIClient:
    """Base class for API clients."""

    def __init__(self, model: str, api_key: str):
        """
        Initialize the API client.
        
        Args:
            model: Model name to use
            api_key: API key for authentication
        """
        self.model = model
        self.api_key = api_key

    def initialize_client(self):
        """Initialize the client. Must be implemented by subclasses."""
        raise NotImplementedError
    
    def send_request(self, prompt: str, **kwargs):
        """
        Send a request to the API.
        
        Args:
            prompt: The prompt to send
            **kwargs: Additional arguments for the API
            
        Returns:
            The API response
        """
        raise NotImplementedError
    

class AnthropicClient(APIClient):
    """Client for the Anthropic API."""
    
    def __init__(self, model: str, api_key: str):
        """
        Initialize the Anthropic client.
        
        Args:
            model: Model name to use
            api_key: API key for authentication
        """
        super().__init__(model, api_key)
        self.client = None
        self.initialize_client()

    def initialize_client(self):
        """Initialize the Anthropic client."""
        try:
            import anthropic
            # Use the Anthropic client initialization
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except Exception as e:
            raise Exception(f"Failed to initialize Anthropic client: {e}")

    def send_request(self, prompt: str, pdf_url=None, **kwargs):
        """
        Send a request to the Anthropic API.
        
        Args:
            prompt: The prompt to send
            pdf_url: Optional URL to a PDF to include in the request
            **kwargs: Additional arguments for the API
            
        Returns:
            The API response
        """
        try:
            # Use the messages API for all requests
            if not pdf_url:
                raise ValueError("pdf_url must be provided for document requests")
                # Make sure the PDF URL uses HTTPS
            
            if pdf_url.startswith('http:'):
                pdf_url = 'https' + pdf_url[4:]
            
            # Simple format using document + text
            response = self.client.messages.create(
                model=self.model,
                max_tokens=kwargs.get('max_tokens_to_sample', 5000),
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "document",
                                "source": {
                                    "type": "url",
                                    "url": pdf_url
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )

            return response.content[0].text
                
        except Exception as e:
            # Simple error handling - just propagate the error
            raise Exception(f"Error calling Anthropic API: {e}")
    
# class OpenAIClient(APIClient):
#     """Client for the OpenAI API."""
    
#     def __init__(self, model: str, api_key: str):
#         """
#         Initialize the OpenAI client.
        
#         Args:
#             model: Model name to use
#             api_key: API key for authentication
#         """
#         super().__init__(model, api_key)
#         self.client = None
#         self.initialize_client()

#     def initialize_client(self):
#         """Initialize the OpenAI client."""
#         try:
#             import openai
#             self.client = openai.OpenAI(api_key=self.api_key)
#         except ImportError:
#             raise ImportError("openai package is required. Install it with 'pip install openai'.")
#         except Exception as e:
#             raise Exception(f"Failed to initialize OpenAI client: {e}")

#     def send_request(self, prompt: str, **kwargs):
#         """
#         Send a request to the OpenAI API.
        
#         Args:
#             prompt: The prompt to send
#             **kwargs: Additional arguments for the API
            
#         Returns:
#             The API response
#         """
#         # Convert from Anthropic parameters to OpenAI parameters if needed
#         if 'max_tokens_to_sample' in kwargs:
#             kwargs['max_tokens'] = kwargs.pop('max_tokens_to_sample')
        
#         # Set default parameters if not provided
#         if 'max_tokens' not in kwargs:
#             kwargs['max_tokens'] = 1000
            
#         # Create the messages array for OpenAI
#         messages = [{"role": "user", "content": prompt}]
        
#         try:
#             response = self.client.chat.completions.create(
#                 model=self.model,
#                 messages=messages,
#                 **kwargs
#             )
#             return response
#         except Exception as e:
#             raise Exception(f"Error calling OpenAI API: {e}")