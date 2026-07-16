package com.autodev.platform.security;

import java.util.UUID;

/** The authenticated principal placed into the SecurityContext by {@link JwtAuthenticationFilter}. */
public record AuthenticatedUser(UUID id, String email) {
}
