package com.autodev.platform;

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

import java.util.Map;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/** Same as ProviderSettingsMissingEncryptionKeyTest, but for a key that's
 * present yet the wrong size (not a multiple/valid AES-256 key). */
@SpringBootTest(properties = "platform.credential-encryption-key=MTIzNDU2Nzg5MDEyMzQ1Ng==")
@AutoConfigureMockMvc
@ActiveProfiles("test")
class ProviderSettingsMalformedEncryptionKeyTest {

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
    void savingApiKey_withMalformedWrongSizeEncryptionKey_fails500() throws Exception {
        String token = registerAndGetToken("malformed-key@example.com");

        mockMvc.perform(post("/api/settings").header("Authorization", "Bearer " + token)
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(Map.of("groqApiKey", "gsk_shouldNeverBeStored"))))
                .andExpect(status().isInternalServerError());
    }
}
