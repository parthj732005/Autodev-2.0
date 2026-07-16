package com.autodev.platform.repository;

import com.autodev.platform.entity.ProviderSettings;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface ProviderSettingsRepository extends JpaRepository<ProviderSettings, UUID> {
    Optional<ProviderSettings> findByUserId(UUID userId);
}
