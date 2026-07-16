package com.autodev.platform.controller;

import com.autodev.platform.dto.ProviderSettingsResponse;
import com.autodev.platform.dto.ResolvedProviderSettingsResponse;
import com.autodev.platform.security.AuthenticatedUser;
import com.autodev.platform.service.ProviderSettingsService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/settings")
public class ProviderSettingsController {

    private final ProviderSettingsService service;

    public ProviderSettingsController(ProviderSettingsService service) {
        this.service = service;
    }

    @GetMapping
    public ResponseEntity<ProviderSettingsResponse> get(@AuthenticationPrincipal AuthenticatedUser principal) {
        return ResponseEntity.ok(service.getMasked(principal.id()));
    }

    /**
     * Full decrypted view. Intended ONLY for FastAPI's platform_client.py,
     * using the same user's own JWT — never called by the React frontend.
     */
    @GetMapping("/resolved")
    public ResponseEntity<ResolvedProviderSettingsResponse> getResolved(
            @AuthenticationPrincipal AuthenticatedUser principal
    ) {
        return ResponseEntity.ok(service.getResolved(principal.id()));
    }

    @PostMapping
    public ResponseEntity<ProviderSettingsResponse> update(
            @AuthenticationPrincipal AuthenticatedUser principal,
            @RequestBody Map<String, Object> body
    ) {
        return ResponseEntity.ok(service.update(principal.id(), body));
    }
}
