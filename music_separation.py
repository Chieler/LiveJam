import demucs.separate
demucs.separate.main(["--mp3", "-o", "audio/output", "--filename", "{track}_{stem}.{ext}", "--two-stems",  "guitar", "-n", "htdemucs_6s", "audio/AC⧸DC - Highway to Hell (Official Video).mp3"])
demucs.separate.main([
    "--mp3", 
     "-o", "audio/output", "--filename", "{track}_{stem}.{ext}",
    "--two-stems", "drums",

    "-n", "mdx_extra", 
    "audio/AC⧸DC - Highway to Hell (Official Video).mp3"
])
