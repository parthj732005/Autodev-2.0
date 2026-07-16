package com.autodev.platform.service;

import com.autodev.platform.dto.ProviderSettingsResponse;
import com.autodev.platform.dto.ResolvedProviderSettingsResponse;
import com.autodev.platform.entity.ProviderSettings;
import com.autodev.platform.entity.User;
import com.autodev.platform.exception.ResourceNotFoundException;
import com.autodev.platform.repository.ProviderSettingsRepository;
import com.autodev.platform.repository.UserRepository;
import com.autodev.platform.security.CredentialEncryptor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Map;
import java.util.UUID;
import java.util.function.Consumer;

@Service
public class ProviderSettingsService {

    private final ProviderSettingsRepository repository;
    private final UserRepository userRepository;
    private final CredentialEncryptor encryptor;

    public ProviderSettingsService(
            ProviderSettingsRepository repository,
            UserRepository userRepository,
            CredentialEncryptor encryptor
    ) {
        this.repository = repository;
        this.userRepository = userRepository;
        this.encryptor = encryptor;
    }

    @Transactional
    public ProviderSettingsResponse getMasked(UUID userId) {
        return toMasked(findOrCreate(userId));
    }

    @Transactional
    public ResolvedProviderSettingsResponse getResolved(UUID userId) {
        ProviderSettings s = findOrCreate(userId);
        return new ResolvedProviderSettingsResponse(
                s.getSelectedProvider(),
                s.getOpenaiModel(), encryptor.decrypt(s.getOpenaiApiKeyEncrypted()),
                s.getAnthropicModel(), encryptor.decrypt(s.getAnthropicApiKeyEncrypted()),
                s.getGroqModel(), encryptor.decrypt(s.getGroqApiKeyEncrypted()),
                s.getHuggingfaceModel(), encryptor.decrypt(s.getHuggingfaceApiKeyEncrypted()),
                s.getOllamaBaseUrl(), s.getOllamaModel()
        );
    }

    @Transactional
    public ProviderSettingsResponse update(UUID userId, Map<String, Object> body) {
        ProviderSettings s = findOrCreate(userId);

        if (body.containsKey("selectedProvider") && body.get("selectedProvider") != null) {
            s.setSelectedProvider(String.valueOf(body.get("selectedProvider")));
        }

        applyPlainField(body, "openaiModel", s::setOpenaiModel);
        applyKeyField(body, "openaiApiKey", s::setOpenaiApiKeyEncrypted);
        applyPlainField(body, "anthropicModel", s::setAnthropicModel);
        applyKeyField(body, "anthropicApiKey", s::setAnthropicApiKeyEncrypted);
        applyPlainField(body, "groqModel", s::setGroqModel);
        applyKeyField(body, "groqApiKey", s::setGroqApiKeyEncrypted);
        applyPlainField(body, "huggingfaceModel", s::setHuggingfaceModel);
        applyKeyField(body, "huggingfaceApiKey", s::setHuggingfaceApiKeyEncrypted);
        applyPlainField(body, "ollamaBaseUrl", s::setOllamaBaseUrl);
        applyPlainField(body, "ollamaModel", s::setOllamaModel);

        return toMasked(repository.save(s));
    }

    private ProviderSettings findOrCreate(UUID userId) {
        return repository.findByUserId(userId).orElseGet(() -> {
            User user = userRepository.findById(userId)
                    .orElseThrow(() -> new ResourceNotFoundException("User not found"));
            ProviderSettings s = new ProviderSettings();
            s.setUser(user);
            s.setSelectedProvider("openai");
            return repository.save(s);
        });
    }

    /** Omitted key -> preserve. Present with null/blank -> clear. Present with a value -> replace. */
    private void applyPlainField(Map<String, Object> body, String key, Consumer<String> setter) {
        if (!body.containsKey(key)) {
            return;
        }
        Object v = body.get(key);
        setter.accept(v == null ? null : String.valueOf(v));
    }

    /** Same omit/clear/replace semantics as applyPlainField, but encrypts non-blank values. */
    private void applyKeyField(Map<String, Object> body, String key, Consumer<String> setter) {
        if (!body.containsKey(key)) {
            return;
        }
        Object v = body.get(key);
        if (v == null || String.valueOf(v).isBlank()) {
            setter.accept(null);
        } else {
            setter.accept(encryptor.encrypt(String.valueOf(v)));
        }
    }

    private ProviderSettingsResponse toMasked(ProviderSettings s) {
        return new ProviderSettingsResponse(
                s.getSelectedProvider(),
                s.getOpenaiModel(), s.getOpenaiApiKeyEncrypted() != null, suffixOf(s.getOpenaiApiKeyEncrypted()),
                s.getAnthropicModel(), s.getAnthropicApiKeyEncrypted() != null, suffixOf(s.getAnthropicApiKeyEncrypted()),
                s.getGroqModel(), s.getGroqApiKeyEncrypted() != null, suffixOf(s.getGroqApiKeyEncrypted()),
                s.getHuggingfaceModel(), s.getHuggingfaceApiKeyEncrypted() != null, suffixOf(s.getHuggingfaceApiKeyEncrypted()),
                s.getOllamaBaseUrl(), s.getOllamaModel()
        );
    }

    private String suffixOf(String encryptedValue) {
        if (encryptedValue == null) {
            return null;
        }
        String plain = encryptor.decrypt(encryptedValue);
        return plain.length() <= 4 ? plain : plain.substring(plain.length() - 4);
    }
}
