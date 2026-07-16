package com.autodev.platform.dto;

import com.autodev.platform.entity.ProjectStatus;
import jakarta.validation.constraints.NotNull;

public record UpdateStatusRequest(@NotNull ProjectStatus status) {
}
