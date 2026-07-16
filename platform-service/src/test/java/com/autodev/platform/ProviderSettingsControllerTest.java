package com.autodev.platform;

import com.autodev.platform.entity.ProviderSettings;
import com.autodev.platform.repository.ProjectRepository;
import com.autodev.platform.repository.ProviderSettingsRepository;
import com.autodev.platform.repository.UserRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import java.util.HashMap;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class ProviderSettingsControllerTest {

    @Autowired private MockMvc mockMvc;
    @Autowired private ObjectMapper objectMapper;
    @Autowired private UserRepository userRepository;
    @Autowired private ProjectRepository projectRepository;
    @Autowired private ProviderSettingsRepository providerSettingsRepository;

    @AfterEach
    void cleanUp() {
        providerSettingsRepository.deleteAll();
        projectRepository.deleteAll();
        userRepository.deleteAll();
    }

    private String registerAndGetToken(String email) throws Exception {
        String body = objectMapper.writeValueAsString(Map.of("email", email, "password", "supersecret1"));
        String response = mockMvc.perform(post("/api/auth/register")
                        .contentType("application/json").content(body))
                .andReturn().getResponse().getContentAsString();
        return objectMapper.readTree(response).get("token").asText();
    }

    @Test
    void get_withoutAuth_returns401() throws Exception {
        mockMvc.perform(get("/api/settings")).andExpect(status().isUnauthorized());
    }

    @Test
    void get_beforeAnyUpdate_returnsDefaultUnconfiguredState() throws Exception {
        String token = registerAndGetToken("fresh@example.com");

        mockMvc.perform(get("/api/settings").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.selectedProvider").value("openai"))
                .andExpect(jsonPath("$.openaiApiKeyConfigured").value(false))
                .andExpect(jsonPath("$.groqApiKeyConfigured").value(false));
    }

    @Test
    void update_setsProviderAndKey_thenGetReflectsMaskedState() throws Exception {
        String token = registerAndGetToken("saver@example.com");

        Map<String, Object> update = new HashMap<>();
        update.put("selectedProvider", "groq");
        update.put("groqModel", "llama-3.3-70b-versatile");
        update.put("groqApiKey", "gsk_realSecretValue1234");

        mockMvc.perform(post("/api/settings")
                        .header("Authorization", "Bearer " + token)
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(update)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.selectedProvider").value("groq"))
                .andExpect(jsonPath("$.groqModel").value("llama-3.3-70b-versatile"))
                .andExpect(jsonPath("$.groqApiKeyConfigured").value(true))
                .andExpect(jsonPath("$.groqApiKeySuffix").value("1234"))
                // The response body itself must never contain the full raw key.
                .andExpect(content().string(org.hamcrest.Matchers.not(
                        org.hamcrest.Matchers.containsString("gsk_realSecretValue1234"))));
    }

    @Test
    void apiKey_isNeverStoredAsPlaintextInDatabase() throws Exception {
        String token = registerAndGetToken("plaintext-check@example.com");
        Map<String, Object> update = Map.of("selectedProvider", "groq", "groqApiKey", "gsk_totallyRealSecret");

        mockMvc.perform(post("/api/settings")
                        .header("Authorization", "Bearer " + token)
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(update)))
                .andExpect(status().isOk());

        ProviderSettings stored = providerSettingsRepository.findAll().stream()
                .filter(s -> s.getGroqApiKeyEncrypted() != null)
                .findFirst().orElseThrow();
        assertThat(stored.getGroqApiKeyEncrypted()).isNotEqualTo("gsk_totallyRealSecret");
        assertThat(stored.getGroqApiKeyEncrypted()).doesNotContain("gsk_totallyRealSecret");
    }

    @Test
    void omittedApiKeyField_preservesExistingKey() throws Exception {
        String token = registerAndGetToken("preserve@example.com");
        mockMvc.perform(post("/api/settings").header("Authorization", "Bearer " + token)
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(
                                Map.of("selectedProvider", "groq", "groqApiKey", "gsk_originalKey"))))
                .andExpect(status().isOk());

        // Update only the model — omit groqApiKey entirely.
        mockMvc.perform(post("/api/settings").header("Authorization", "Bearer " + token)
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(Map.of("groqModel", "llama-3.1-8b-instant"))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.groqApiKeyConfigured").value(true))
                .andExpect(jsonPath("$.groqApiKeySuffix").value("lKey"));
    }

    @Test
    void replacingApiKey_updatesStoredValue() throws Exception {
        String token = registerAndGetToken("replace@example.com");
        mockMvc.perform(post("/api/settings").header("Authorization", "Bearer " + token)
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(Map.of("groqApiKey", "gsk_firstKey"))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.groqApiKeySuffix").value("tKey"));

        mockMvc.perform(post("/api/settings").header("Authorization", "Bearer " + token)
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(Map.of("groqApiKey", "gsk_brandNewKey"))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.groqApiKeySuffix").value("wKey"));
    }

    @Test
    void explicitNullApiKey_clearsStoredKey() throws Exception {
        String token = registerAndGetToken("clear@example.com");
        mockMvc.perform(post("/api/settings").header("Authorization", "Bearer " + token)
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(Map.of("groqApiKey", "gsk_toBeCleared"))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.groqApiKeyConfigured").value(true));

        Map<String, Object> clearBody = new HashMap<>();
        clearBody.put("groqApiKey", null);
        mockMvc.perform(post("/api/settings").header("Authorization", "Bearer " + token)
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(clearBody)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.groqApiKeyConfigured").value(false))
                .andExpect(jsonPath("$.groqApiKeySuffix").doesNotExist());
    }

    @Test
    void twoUsers_haveIndependentSettings() throws Exception {
        String tokenA = registerAndGetToken("settings-a@example.com");
        String tokenB = registerAndGetToken("settings-b@example.com");

        mockMvc.perform(post("/api/settings").header("Authorization", "Bearer " + tokenA)
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(
                                Map.of("selectedProvider", "openai", "openaiApiKey", "sk-userAKey"))))
                .andExpect(status().isOk());

        mockMvc.perform(post("/api/settings").header("Authorization", "Bearer " + tokenB)
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(
                                Map.of("selectedProvider", "groq", "groqApiKey", "gsk_userBKey"))))
                .andExpect(status().isOk());

        // User A's own view is unaffected by User B's update.
        mockMvc.perform(get("/api/settings").header("Authorization", "Bearer " + tokenA))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.selectedProvider").value("openai"))
                .andExpect(jsonPath("$.openaiApiKeyConfigured").value(true))
                .andExpect(jsonPath("$.groqApiKeyConfigured").value(false));

        mockMvc.perform(get("/api/settings").header("Authorization", "Bearer " + tokenB))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.selectedProvider").value("groq"))
                .andExpect(jsonPath("$.groqApiKeyConfigured").value(true))
                .andExpect(jsonPath("$.openaiApiKeyConfigured").value(false));
    }

    @Test
    void changingUserAProvider_doesNotAffectUserB() throws Exception {
        String tokenA = registerAndGetToken("indep-a@example.com");
        String tokenB = registerAndGetToken("indep-b@example.com");

        mockMvc.perform(post("/api/settings").header("Authorization", "Bearer " + tokenB)
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(Map.of("selectedProvider", "anthropic"))))
                .andExpect(status().isOk());

        mockMvc.perform(post("/api/settings").header("Authorization", "Bearer " + tokenA)
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(Map.of("selectedProvider", "huggingface"))))
                .andExpect(status().isOk());

        mockMvc.perform(get("/api/settings").header("Authorization", "Bearer " + tokenB))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.selectedProvider").value("anthropic"));
    }

    @Test
    void resolvedEndpoint_withoutAuth_returns401() throws Exception {
        mockMvc.perform(get("/api/settings/resolved")).andExpect(status().isUnauthorized());
    }

    @Test
    void resolvedEndpoint_returnsRealDecryptedKey_forTheOwningUserOnly() throws Exception {
        String token = registerAndGetToken("resolved@example.com");
        mockMvc.perform(post("/api/settings").header("Authorization", "Bearer " + token)
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(
                                Map.of("selectedProvider", "groq", "groqApiKey", "gsk_realDecryptedValue"))))
                .andExpect(status().isOk());

        mockMvc.perform(get("/api/settings/resolved").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.selectedProvider").value("groq"))
                .andExpect(jsonPath("$.groqApiKey").value("gsk_realDecryptedValue"));
    }
}
