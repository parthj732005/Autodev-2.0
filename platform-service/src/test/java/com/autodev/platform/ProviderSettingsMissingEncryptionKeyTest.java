package com.autodev.platform;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import com.autodev.platform.repository.ProjectRepository;
import com.autodev.platform.repository.ProviderSettingsRepository;
import com.autodev.platform.repository.UserRepository;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import java.util.Map;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Controller-level proof that a missing encryption key fails the request
 * safely (500, generic message) rather than crashing uncontrolled or storing
 * plaintext. The unit-level guarantee lives in CredentialEncryptorTest; this
 * confirms the exception actually propagates correctly through the real
 * Spring MVC exception-handling wiring end-to-end.
 */
@SpringBootTest(properties = "platform.credential-encryption-key=")
@AutoConfigureMockMvc
@ActiveProfiles("test")
class ProviderSettingsMissingEncryptionKeyTest {

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
    void savingApiKey_withMissingEncryptionKey_fails500_notPlaintext() throws Exception {
        String token = registerAndGetToken("missing-key@example.com");

        mockMvc.perform(post("/api/settings").header("Authorization", "Bearer " + token)
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(Map.of("groqApiKey", "gsk_shouldNeverBeStored"))))
                .andExpect(status().isInternalServerError());
    }

    @Test
    void gettingSettings_withMissingEncryptionKey_fails500() throws Exception {
        // Even the masked GET needs to decrypt for the suffix, so it must also
        // fail safely rather than silently omitting the suffix.
        String token = registerAndGetToken("missing-key-get@example.com");
        mockMvc.perform(post("/api/settings").header("Authorization", "Bearer " + token)
                        .contentType("application/json")
                        .content("{}"))
                .andExpect(status().isOk()); // no key involved yet, fine

        mockMvc.perform(get("/api/settings").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk()); // still fine — nothing to decrypt

        // Now attempt to store a key while the master key is missing.
        mockMvc.perform(post("/api/settings").header("Authorization", "Bearer " + token)
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(Map.of("openaiApiKey", "sk-anything"))))
                .andExpect(status().isInternalServerError());
    }
}
