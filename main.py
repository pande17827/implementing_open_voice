import os
import torch
from openvoice import se_extractor
from openvoice.api import ToneColorConverter
from melo.api import TTS
import nltk
nltk.download('averaged_perceptron_tagger_eng')
# Setup
ckpt_converter = 'checkpoints_v2/converter'
device = "cuda:0" if torch.cuda.is_available() else "cpu"
output_dir = 'outputs_v2'
os.makedirs(output_dir, exist_ok=True)

# Load tone color converter
tone_color_converter = ToneColorConverter(f'{ckpt_converter}/config.json', device=device)
tone_color_converter.load_ckpt(f'{ckpt_converter}/checkpoint.pth')

# Target voice reference
reference_speaker = 'resources/example_reference.mp3'  # Voice to clone
target_se, audio_name = se_extractor.get_se(reference_speaker, tone_color_converter, vad=False)

# Input texts for each language
texts = {
    'EN_NEWEST': "Did you ever hear a folk tale about a giant turtle?",
    'EN': "Did you ever hear a folk tale about a giant turtle?",
    'ES': "El resplandor del sol acaricia las olas, pintando el cielo con una paleta deslumbrante.",
    'FR': "La lueur dorée du soleil caresse les vagues, peignant le ciel d'une palette éblouissante.",
    'ZH': "在这次vacation中，我们计划去Paris欣赏埃菲尔铁塔和卢浮宫的美景。",
    'JP': "彼は毎朝ジョギングをして体を健康に保っています。",
    'KR': "안녕하세요! 오늘은 날씨가 정말 좋네요.",
}

# Temp output for TTS before conversion
src_path = f'{output_dir}/tmp.wav'
speed = 1.0
encode_message = "@MyShell"

# Voice generation loop
for language, text in texts.items():
    model = TTS(language=language, device=device)
    speaker_ids = model.hps.data.spk2id

    for speaker_key in speaker_ids.keys():
        speaker_id = speaker_ids[speaker_key]
        speaker_key_formatted = speaker_key.lower().replace('_', '-')

        source_se = torch.load(
            f'checkpoints_v2/base_speakers/ses/{speaker_key_formatted}.pth',
            map_location=device
        )

        # TTS output
        model.tts_to_file(text, speaker_id, src_path, speed=speed)

        # Final save path
        save_path = f'{output_dir}/output_v2_{speaker_key_formatted}.wav'

        # Tone color conversion
        tone_color_converter.convert(
            audio_src_path=src_path,
            src_se=source_se,
            tgt_se=target_se,
            output_path=save_path,
            message=encode_message
        )

print("✅ Voice conversion completed for all speakers.")
