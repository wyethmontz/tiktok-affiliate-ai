from workflows.ad_pipeline import run_pipeline

input_data = {
    "product": "Lip Tint",
    "audience": "Gen Z women",
    "platform": "TikTok",
    "goal": "Increase sales"
}

result = run_pipeline(input_data)

print("\n=== RESULT ===\n")
print(result)