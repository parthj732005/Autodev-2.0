package com.autodev.platform.controller;

import com.autodev.platform.dto.CreateProjectRequest;
import com.autodev.platform.dto.ProjectResponse;
import com.autodev.platform.dto.UpdateStatusRequest;
import com.autodev.platform.security.AuthenticatedUser;
import com.autodev.platform.service.ProjectService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/projects")
public class ProjectController {

    private final ProjectService projectService;

    public ProjectController(ProjectService projectService) {
        this.projectService = projectService;
    }

    @PostMapping
    public ResponseEntity<ProjectResponse> create(
            @AuthenticationPrincipal AuthenticatedUser principal,
            @Valid @RequestBody CreateProjectRequest request
    ) {
        return ResponseEntity.status(HttpStatus.CREATED).body(projectService.create(principal.id(), request));
    }

    @GetMapping
    public ResponseEntity<List<ProjectResponse>> list(@AuthenticationPrincipal AuthenticatedUser principal) {
        return ResponseEntity.ok(projectService.listForUser(principal.id()));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ProjectResponse> get(
            @AuthenticationPrincipal AuthenticatedUser principal,
            @PathVariable UUID id
    ) {
        return ResponseEntity.ok(projectService.getOwned(principal.id(), id));
    }

    @GetMapping("/by-key/{projectKey}")
    public ResponseEntity<ProjectResponse> getByKey(
            @AuthenticationPrincipal AuthenticatedUser principal,
            @PathVariable String projectKey
    ) {
        return ResponseEntity.ok(projectService.getOwnedByKey(principal.id(), projectKey));
    }

    @PatchMapping("/{id}/status")
    public ResponseEntity<ProjectResponse> updateStatus(
            @AuthenticationPrincipal AuthenticatedUser principal,
            @PathVariable UUID id,
            @Valid @RequestBody UpdateStatusRequest request
    ) {
        return ResponseEntity.ok(projectService.updateStatus(principal.id(), id, request));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(
            @AuthenticationPrincipal AuthenticatedUser principal,
            @PathVariable UUID id
    ) {
        projectService.delete(principal.id(), id);
        return ResponseEntity.noContent().build();
    }
}
