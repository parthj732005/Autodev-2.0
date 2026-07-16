package com.autodev.platform.dto;

/**
 * Full decrypted view — used ONLY by FastAPI's platform_client.py, on behalf
 * of the same authenticated user whose JWT was presented (never exposed to
 * the React frontend, which only ever calls the masked endpoint).
 */
public record ResolvedProviderSettingsResponse(
        String selectedProvider,
        String openaiModel, String openaiApiKey,
        String anthropicModel, String anthropicApiKey,
        String groqModel, String groqApiKey,
        String huggingfaceModel, String huggingfaceApiKey,
        String ollamaBaseUrl, String ollamaModel
) {
}
