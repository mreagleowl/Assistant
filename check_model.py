import whisper
m = whisper.load_model("large")
print("Loaded model name:", getattr(m, 'name', None))
