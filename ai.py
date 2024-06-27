from pathlib import Path
from gpt4all import GPT4All

class Ai:
    def __init__(self, system_prompt: str | None = None, temp: int | None = None):
        # model_id = "nomic-embed-text-v1.5.f16.gguf"  # No text generation; 1GB
        # model_id = "nous-hermes-llama2-13b.Q4_0.gguf"  # Extremely good model. Instruction based. Gives long responses; 16GB # Favorite Censored
        # model_id = "wizardlm-13b-v1.2.Q4_0.gguf"  # Strong overall larger model. Instruction based. Gives very long responses; 16GB # Favorite Uncensored
        # model_id = "orca-mini-3b-gguf2-q4_0.gguf"  # Small version of new model with novel dataset. Very fast responses; 4GB
        # model_id = "gpt4all-falcon-newbpe-q4_0.gguf"  # Very fast model with good quality. Fastest responses; 8GB
        # model_id = "orca-2-13b.Q4_0.gguf"  # Instruction Based. Model for work applications; 16GB
        # model_id = "ghost-7b-v0.9.1-Q4_0.gguf"  # taiwan orso
        # model_id = "gpt4all-13b-snoozy-q4_0.gguf"
        # model_id = "Lexi-Llama-3-8B-Uncensored-Q6_K.gguf"  # Uncensored but breaks ALOT
        model_id = "Lexi-Llama-3-8B-Uncensored-Q5_K_S.gguf"  # Uncensored but annoying template unstable with breaking
        # model_id = "lostmagic-rp_7b.Q4_K_M.gguf"  # Breaking
        # model_id = "Prima-LelantaclesV6-7b-Q4_K_S-imatrix.gguf"  # Doesnt roleplay
        # model_id = "13b-ouroboros.Q4_K_S.gguf"  # No Roleplaying

        self.model = GPT4All(model_id, device='cuda', n_ctx=4096, allow_download=False, model_path=Path.cwd() / 'models')
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

    def generate(self, prompt: str, user: str, date: str):
        if self.system_prompt:
            prompt = (f'### System: {self.system_prompt}'
                      f'### User: My name is {user}. Today is {date} (dont give away that information unless asked for it). {prompt}.')
        if self.temp is not None:
            temp = self.temp
        else:
            temp = 0.7
            prompt = (f'### System: {self.system_prompt}'
                      f'### User: My name is {user}. Today is {date} (dont give away that information unless asked for it). {prompt}.')
        # print(f"Generating {prompt=}")
        # return self.model.generate(prompt=prompt, temp=temp, streaming=True, max_tokens=200, repeat_penalty=1.18, n_batch=8)  # Default
        return self.model.generate(prompt=prompt, temp=temp, streaming=True, max_tokens=200, repeat_penalty=1.18, n_batch=8)  # Custom
