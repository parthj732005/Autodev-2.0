package com.autodev.platform.entity;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;

/**
 * One row per user. Mirrors the fields the original backend/settings.json
 * supported for each of the 5 providers (model + credential per provider,
 * plus which one is currently selected) so existing provider-selection
 * behavior is preserved — just scoped per-user instead of global, and with
 * API keys stored AES-GCM encrypted (see CredentialEncryptor) rather than
 * plaintext.
 */
@Entity
@Table(name = "provider_settings")
public class ProviderSettings {

    @Id
    @GeneratedValue
    private UUID id;

    @OneToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id", nullable = false, unique = true)
    private User user;

    @Column(name = "selected_provider", nullable = false)
    private String selectedProvider = "openai";

    @Column(name = "openai_model")
    private String openaiModel;
    @Column(name = "openai_api_key_encrypted")
    private String openaiApiKeyEncrypted;

    @Column(name = "anthropic_model")
    private String anthropicModel;
    @Column(name = "anthropic_api_key_encrypted")
    private String anthropicApiKeyEncrypted;

    @Column(name = "groq_model")
    private String groqModel;
    @Column(name = "groq_api_key_encrypted")
    private String groqApiKeyEncrypted;

    @Column(name = "huggingface_model")
    private String huggingfaceModel;
    @Column(name = "huggingface_api_key_encrypted")
    private String huggingfaceApiKeyEncrypted;

    @Column(name = "ollama_base_url")
    private String ollamaBaseUrl;
    @Column(name = "ollama_model")
    private String ollamaModel;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    @PrePersist
    void onCreate() {
        Instant now = Instant.now();
        createdAt = now;
        updatedAt = now;
    }

    @PreUpdate
    void onUpdate() {
        updatedAt = Instant.now();
    }

    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }

    public User getUser() { return user; }
    public void setUser(User user) { this.user = user; }

    public String getSelectedProvider() { return selectedProvider; }
    public void setSelectedProvider(String selectedProvider) { this.selectedProvider = selectedProvider; }

    public String getOpenaiModel() { return openaiModel; }
    public void setOpenaiModel(String openaiModel) { this.openaiModel = openaiModel; }

    public String getOpenaiApiKeyEncrypted() { return openaiApiKeyEncrypted; }
    public void setOpenaiApiKeyEncrypted(String v) { this.openaiApiKeyEncrypted = v; }

    public String getAnthropicModel() { return anthropicModel; }
    public void setAnthropicModel(String anthropicModel) { this.anthropicModel = anthropicModel; }

    public String getAnthropicApiKeyEncrypted() { return anthropicApiKeyEncrypted; }
    public void setAnthropicApiKeyEncrypted(String v) { this.anthropicApiKeyEncrypted = v; }

    public String getGroqModel() { return groqModel; }
    public void setGroqModel(String groqModel) { this.groqModel = groqModel; }

    public String getGroqApiKeyEncrypted() { return groqApiKeyEncrypted; }
    public void setGroqApiKeyEncrypted(String v) { this.groqApiKeyEncrypted = v; }

    public String getHuggingfaceModel() { return huggingfaceModel; }
    public void setHuggingfaceModel(String huggingfaceModel) { this.huggingfaceModel = huggingfaceModel; }

    public String getHuggingfaceApiKeyEncrypted() { return huggingfaceApiKeyEncrypted; }
    public void setHuggingfaceApiKeyEncrypted(String v) { this.huggingfaceApiKeyEncrypted = v; }

    public String getOllamaBaseUrl() { return ollamaBaseUrl; }
    public void setOllamaBaseUrl(String ollamaBaseUrl) { this.ollamaBaseUrl = ollamaBaseUrl; }

    public String getOllamaModel() { return ollamaModel; }
    public void setOllamaModel(String ollamaModel) { this.ollamaModel = ollamaModel; }

    public Instant getCreatedAt() { return createdAt; }
    public Instant getUpdatedAt() { return updatedAt; }
}
