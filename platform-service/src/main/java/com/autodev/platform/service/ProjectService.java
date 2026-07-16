package com.autodev.platform.service;

import com.autodev.platform.dto.CreateProjectRequest;
import com.autodev.platform.dto.ProjectResponse;
import com.autodev.platform.dto.UpdateStatusRequest;
import com.autodev.platform.entity.Project;
import com.autodev.platform.entity.User;
import com.autodev.platform.exception.DuplicateProjectKeyException;
import com.autodev.platform.exception.ResourceNotFoundException;
import com.autodev.platform.repository.ProjectRepository;
import com.autodev.platform.repository.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

@Service
public class ProjectService {

    private final ProjectRepository projectRepository;
    private final UserRepository userRepository;

    public ProjectService(ProjectRepository projectRepository, UserRepository userRepository) {
        this.projectRepository = projectRepository;
        this.userRepository = userRepository;
    }

    @Transactional
    public ProjectResponse create(UUID userId, CreateProjectRequest request) {
        if (projectRepository.existsByProjectKey(request.projectKey())) {
            throw new DuplicateProjectKeyException(request.projectKey());
        }

        User user = userRepository.findById(userId)
                .orElseThrow(() -> new ResourceNotFoundException("User not found"));

        Project project = new Project();
        project.setProjectKey(request.projectKey());
        project.setUser(user);
        project.setName(request.name());
        project.setTechStack(request.techStack());
        project.setOutputPath(request.outputPath());

        return ProjectResponse.from(projectRepository.save(project));
    }

    @Transactional(readOnly = true)
    public List<ProjectResponse> listForUser(UUID userId) {
        return projectRepository.findByUserIdOrderByCreatedAtDesc(userId).stream()
                .map(ProjectResponse::from)
                .toList();
    }

    @Transactional(readOnly = true)
    public ProjectResponse getOwned(UUID userId, UUID projectId) {
        return ProjectResponse.from(findOwnedOrThrow(userId, projectId));
    }

    @Transactional(readOnly = true)
    public ProjectResponse getOwnedByKey(UUID userId, String projectKey) {
        Project project = projectRepository.findByProjectKeyAndUserId(projectKey, userId)
                .orElseThrow(() -> new ResourceNotFoundException("Project not found"));
        return ProjectResponse.from(project);
    }

    @Transactional
    public ProjectResponse updateStatus(UUID userId, UUID projectId, UpdateStatusRequest request) {
        Project project = findOwnedOrThrow(userId, projectId);
        project.setStatus(request.status());
        if (request.status() == com.autodev.platform.entity.ProjectStatus.COMPLETED
                || request.status() == com.autodev.platform.entity.ProjectStatus.FAILED) {
            project.setCompletedAt(Instant.now());
        }
        return ProjectResponse.from(projectRepository.save(project));
    }

    @Transactional
    public void delete(UUID userId, UUID projectId) {
        Project project = findOwnedOrThrow(userId, projectId);
        projectRepository.delete(project);
    }

    /**
     * Looks up a project scoped to its owner in one query — a project that
     * exists but belongs to another user returns the same "not found" result
     * as one that doesn't exist at all, so ownership is never leaked via
     * a 403-vs-404 distinction.
     */
    private Project findOwnedOrThrow(UUID userId, UUID projectId) {
        return projectRepository.findByIdAndUserId(projectId, userId)
                .orElseThrow(() -> new ResourceNotFoundException("Project not found"));
    }
}
