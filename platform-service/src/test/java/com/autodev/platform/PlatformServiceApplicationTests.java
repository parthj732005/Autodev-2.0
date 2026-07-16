package com.autodev.platform;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

@SpringBootTest
@ActiveProfiles("test")
class PlatformServiceApplicationTests {

    @Test
    void contextLoads() {
        // Fails the build if the Spring application context (JPA, Security, JWT
        // config, controllers) cannot wire up correctly.
    }
}
