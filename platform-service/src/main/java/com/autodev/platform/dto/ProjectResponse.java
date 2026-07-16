package com.autodev.platform.dto;

import com.autodev.platform.entity.Project;
import com.autodev.platform.entity.ProjectStatus;

import java.time.Instant;
import java.util.UUID;

public record ProjectResponse(
        UUID id,
        String projectKey,
        String name,
        ProjectStatus status,
        String techStack,
        String outputPath,
        Instant createdAt,
        Instant completedAt
) {
    public static ProjectResponse from(Project p) {
        return new ProjectResponse(
                p.getId(),
                p.getProjectKey(),
                p.getName(),
                p.getStatus(),
                p.getTechStack(),
                p.getOutputPath(),
                p.getCreatedAt(),
                p.getCompletedAt()
        );
    }
}
