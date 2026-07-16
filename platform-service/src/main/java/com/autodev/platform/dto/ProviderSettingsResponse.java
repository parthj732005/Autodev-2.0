package com.autodev.platform.dto;

/** Masked view — used by the React Settings page. Never carries a full API key. */
public record ProviderSettingsResponse(
        String selectedProvider,
        String openaiModel, boolean openaiApiKeyConfigured, String openaiApiKeySuffix,
        String anthropicModel, boolean anthropicApiKeyConfigured, String anthropicApiKeySuffix,
        String groqModel, boolean groqApiKeyConfigured, String groqApiKeySuffix,
        String huggingfaceModel, boolean huggingfaceApiKeyConfigured, String huggingfaceApiKeySuffix,
        String ollamaBaseUrl, String ollamaModel
) {
}
