package com.autodev.platform;

import com.autodev.platform.repository.ProjectRepository;
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

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class ProjectControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private ProjectRepository projectRepository;

    @Autowired
    private UserRepository userRepository;

    @AfterEach
    void cleanUp() {
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

    private String createProject(String token, String projectKey, String name) throws Exception {
        String body = objectMapper.writeValueAsString(Map.of(
                "projectKey", projectKey,
                "name", name,
                "techStack", "fastapi+react",
                "outputPath", "/tmp/" + projectKey
        ));
        String response = mockMvc.perform(post("/api/projects")
                        .header("Authorization", "Bearer " + token)
                        .contentType("application/json").content(body))
                .andExpect(status().isCreated())
                .andReturn().getResponse().getContentAsString();
        return objectMapper.readTree(response).get("id").asText();
    }

    @Test
    void createProject_withoutAuth_returns401() throws Exception {
        String body = objectMapper.writeValueAsString(Map.of(
                "projectKey", "no-auth-project", "name", "X"));
        mockMvc.perform(post("/api/projects").contentType("application/json").content(body))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void listProjects_onlyReturnsCallersOwnProjects() throws Exception {
        String tokenA = registerAndGetToken("owner-a@example.com");
        String tokenB = registerAndGetToken("owner-b@example.com");

        createProject(tokenA, "proj-a-1", "A's project");
        createProject(tokenB, "proj-b-1", "B's project");

        mockMvc.perform(get("/api/projects").header("Authorization", "Bearer " + tokenA))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()").value(1))
                .andExpect(jsonPath("$[0].projectKey").value("proj-a-1"));
    }

    @Test
    void getProject_byOwner_returns200() throws Exception {
        String token = registerAndGetToken("owner-c@example.com");
        String id = createProject(token, "proj-c-1", "C's project");

        mockMvc.perform(get("/api/projects/" + id).header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.projectKey").value("proj-c-1"));
    }

    @Test
    void getProject_byNonOwner_returns404() throws Exception {
        String ownerToken = registerAndGetToken("owner-d@example.com");
        String intruderToken = registerAndGetToken("intruder-d@example.com");
        String id = createProject(ownerToken, "proj-d-1", "D's project");

        mockMvc.perform(get("/api/projects/" + id).header("Authorization", "Bearer " + intruderToken))
                .andExpect(status().isNotFound());
    }

    @Test
    void patchStatus_byNonOwner_returns404_andDoesNotChangeStatus() throws Exception {
        String ownerToken = registerAndGetToken("owner-e@example.com");
        String intruderToken = registerAndGetToken("intruder-e@example.com");
        String id = createProject(ownerToken, "proj-e-1", "E's project");

        String patchBody = objectMapper.writeValueAsString(Map.of("status", "COMPLETED"));
        mockMvc.perform(patch("/api/projects/" + id + "/status")
                        .header("Authorization", "Bearer " + intruderToken)
                        .contentType("application/json").content(patchBody))
                .andExpect(status().isNotFound());

        // Confirm the owner still sees the original status (unaffected by the rejected attempt)
        mockMvc.perform(get("/api/projects/" + id).header("Authorization", "Bearer " + ownerToken))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("PENDING"));
    }

    @Test
    void patchStatus_byOwner_updatesStatusAndSetsCompletedAt() throws Exception {
        String token = registerAndGetToken("owner-f@example.com");
        String id = createProject(token, "proj-f-1", "F's project");

        String patchBody = objectMapper.writeValueAsString(Map.of("status", "COMPLETED"));
        mockMvc.perform(patch("/api/projects/" + id + "/status")
                        .header("Authorization", "Bearer " + token)
                        .contentType("application/json").content(patchBody))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("COMPLETED"))
                .andExpect(jsonPath("$.completedAt").isNotEmpty());
    }

    @Test
    void deleteProject_byNonOwner_returns404_andProjectStillExistsForOwner() throws Exception {
        String ownerToken = registerAndGetToken("owner-g@example.com");
        String intruderToken = registerAndGetToken("intruder-g@example.com");
        String id = createProject(ownerToken, "proj-g-1", "G's project");

        mockMvc.perform(delete("/api/projects/" + id).header("Authorization", "Bearer " + intruderToken))
                .andExpect(status().isNotFound());

        mockMvc.perform(get("/api/projects/" + id).header("Authorization", "Bearer " + ownerToken))
                .andExpect(status().isOk());
    }

    @Test
    void deleteProject_byOwner_returns204_andSubsequentGetReturns404() throws Exception {
        String token = registerAndGetToken("owner-h@example.com");
        String id = createProject(token, "proj-h-1", "H's project");

        mockMvc.perform(delete("/api/projects/" + id).header("Authorization", "Bearer " + token))
                .andExpect(status().isNoContent());

        mockMvc.perform(get("/api/projects/" + id).header("Authorization", "Bearer " + token))
                .andExpect(status().isNotFound());
    }

    @Test
    void getByKey_byOwner_returns200() throws Exception {
        String token = registerAndGetToken("bykey-owner@example.com");
        createProject(token, "bykey-proj-1", "By-key project");

        mockMvc.perform(get("/api/projects/by-key/bykey-proj-1").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.projectKey").value("bykey-proj-1"));
    }

    @Test
    void getByKey_byNonOwner_returns404() throws Exception {
        String ownerToken = registerAndGetToken("bykey-owner2@example.com");
        String intruderToken = registerAndGetToken("bykey-intruder@example.com");
        createProject(ownerToken, "bykey-proj-2", "By-key project 2");

        mockMvc.perform(get("/api/projects/by-key/bykey-proj-2").header("Authorization", "Bearer " + intruderToken))
                .andExpect(status().isNotFound());
    }

    @Test
    void getByKey_forNonexistentKey_returns404() throws Exception {
        String token = registerAndGetToken("bykey-missing@example.com");

        mockMvc.perform(get("/api/projects/by-key/does-not-exist").header("Authorization", "Bearer " + token))
                .andExpect(status().isNotFound());
    }

    @Test
    void createProject_withDuplicateProjectKey_returns409() throws Exception {
        String token = registerAndGetToken("owner-i@example.com");
        createProject(token, "dup-key", "First");

        String body = objectMapper.writeValueAsString(Map.of("projectKey", "dup-key", "name", "Second"));
        mockMvc.perform(post("/api/projects")
                        .header("Authorization", "Bearer " + token)
                        .contentType("application/json").content(body))
                .andExpect(status().isConflict());
    }
}
