package com.autodev.platform.dto;

import jakarta.validation.constraints.NotBlank;

public record CreateProjectRequest(
        @NotBlank String projectKey,
        @NotBlank String name,
        String techStack,
        String outputPath
) {
}
