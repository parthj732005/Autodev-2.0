package com.autodev.platform;

import com.autodev.platform.entity.User;
import com.autodev.platform.repository.ProjectRepository;
import com.autodev.platform.repository.UserRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import java.util.Map;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class AuthControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private ProjectRepository projectRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    @AfterEach
    void cleanUp() {
        projectRepository.deleteAll();
        userRepository.deleteAll();
    }

    private String registerAndGetToken(String email, String password) throws Exception {
        String body = objectMapper.writeValueAsString(Map.of("email", email, "password", password));
        String response = mockMvc.perform(post("/api/auth/register")
                        .contentType("application/json")
                        .content(body))
                .andReturn().getResponse().getContentAsString();
        return objectMapper.readTree(response).get("token").asText();
    }

    @Test
    void register_withNewEmail_returns201WithTokenAndUserId() throws Exception {
        String body = objectMapper.writeValueAsString(Map.of("email", "alice@example.com", "password", "supersecret1"));

        mockMvc.perform(post("/api/auth/register")
                        .contentType("application/json")
                        .content(body))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.token").isNotEmpty())
                .andExpect(jsonPath("$.userId").isNotEmpty())
                .andExpect(jsonPath("$.email").value("alice@example.com"));
    }

    @Test
    void register_withDuplicateEmail_returns409() throws Exception {
        String body = objectMapper.writeValueAsString(Map.of("email", "bob@example.com", "password", "supersecret1"));

        mockMvc.perform(post("/api/auth/register").contentType("application/json").content(body))
                .andExpect(status().isCreated());

        mockMvc.perform(post("/api/auth/register").contentType("application/json").content(body))
                .andExpect(status().isConflict());
    }

    @Test
    void register_hashesPasswordWithBcrypt_neverStoresPlainText() throws Exception {
        String rawPassword = "supersecret1";
        String body = objectMapper.writeValueAsString(Map.of("email", "carol@example.com", "password", rawPassword));

        mockMvc.perform(post("/api/auth/register").contentType("application/json").content(body))
                .andExpect(status().isCreated());

        User stored = userRepository.findByEmail("carol@example.com").orElseThrow();
        assertThat(stored.getPasswordHash()).isNotEqualTo(rawPassword);
        assertThat(stored.getPasswordHash()).startsWith("$2"); // BCrypt hash prefix
        assertThat(passwordEncoder.matches(rawPassword, stored.getPasswordHash())).isTrue();
    }

    @Test
    void login_withValidCredentials_returns200WithToken() throws Exception {
        String registerBody = objectMapper.writeValueAsString(Map.of("email", "dave@example.com", "password", "correcthorse1"));
        mockMvc.perform(post("/api/auth/register").contentType("application/json").content(registerBody))
                .andExpect(status().isCreated());

        String loginBody = objectMapper.writeValueAsString(Map.of("email", "dave@example.com", "password", "correcthorse1"));
        mockMvc.perform(post("/api/auth/login").contentType("application/json").content(loginBody))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.token").isNotEmpty())
                .andExpect(jsonPath("$.email").value("dave@example.com"));
    }

    @Test
    void login_withWrongPassword_returns401() throws Exception {
        String registerBody = objectMapper.writeValueAsString(Map.of("email", "erin@example.com", "password", "correctpass1"));
        mockMvc.perform(post("/api/auth/register").contentType("application/json").content(registerBody))
                .andExpect(status().isCreated());

        String loginBody = objectMapper.writeValueAsString(Map.of("email", "erin@example.com", "password", "wrongpass1"));
        mockMvc.perform(post("/api/auth/login").contentType("application/json").content(loginBody))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void login_withUnknownEmail_returns401() throws Exception {
        String loginBody = objectMapper.writeValueAsString(Map.of("email", "ghost@example.com", "password", "whatever1"));
        mockMvc.perform(post("/api/auth/login").contentType("application/json").content(loginBody))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void me_withoutToken_returns401() throws Exception {
        mockMvc.perform(get("/api/auth/me"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void me_withInvalidToken_returns401() throws Exception {
        mockMvc.perform(get("/api/auth/me").header("Authorization", "Bearer not-a-real-token"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void me_withValidToken_returns200WithOwnEmail() throws Exception {
        String token = registerAndGetToken("frank@example.com", "supersecret1");

        mockMvc.perform(get("/api/auth/me").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.email").value("frank@example.com"));
    }
}
