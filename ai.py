from gpt4all import GPT4All

class Ai:
    def __init__(self, system_prompt: str | None = None, temp: int | None = None):
        # model_id = "nomic-embed-text-v1.5.f16.gguf"  # No text generation
        model_id = "nous-hermes-llama2-13b.Q4_0.gguf"  # uncensored
        # model_id = "wizardlm-13b-v1.2.Q4_0.gguf"  # GPT-3
        # model_id = "orca-mini-3b-gguf2-q4_0.gguf"  # Annoying
        self.model = GPT4All(model_id, device='gpu')
        self.system_prompt = system_prompt
        self.temp = temp

    def __enter__(self):
        self.chat_session = self.model.chat_session()
        self.chat_session.__enter__()
        return self

    def __exit__(self, typ, value, traceback):
        self.chat_session.__exit__(typ, value, traceback)

    def reset(self):
        self.__exit__(None, None, None)
        self.__enter__()

    def set_system_prompt(self, system_prompt: str | None = None):
        print(f"Setting system prompt to {system_prompt=}")
        self.system_prompt = system_prompt
        self.reset()

    def set_temp(self, temp: int | None):
        self.temp = temp
        self.reset()

    def generate(self, prompt: str, user: str):
        if self.system_prompt:
            prompt = (f'### System: {self.system_prompt}'
                      f'### User: My name is {user}. Its Pride Month. {prompt}')
        if self.temp is not None:
            temp = self.temp
        else:
            temp = 0.7
            prompt = f'## User: My name is {user}. {prompt}'
        # print(f"Generating {prompt=}")
        return self.model.generate(prompt=prompt, temp=temp, streaming=True, max_tokens=65536)
