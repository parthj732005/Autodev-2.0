package com.autodev.platform;

import com.autodev.platform.exception.CredentialEncryptionException;
import com.autodev.platform.security.CredentialEncryptor;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class CredentialEncryptorTest {

    private static final String VALID_KEY = "sEERC50Wu/tczhsVl7/Wnf3SdKshXqsairU20DZonDk=";

    @Test
    void encryptThenDecrypt_returnsOriginalPlaintext() {
        CredentialEncryptor encryptor = new CredentialEncryptor(VALID_KEY);

        String encrypted = encryptor.encrypt("sk-super-secret-value");

        assertThat(encrypted).isNotEqualTo("sk-super-secret-value");
        assertThat(encryptor.decrypt(encrypted)).isEqualTo("sk-super-secret-value");
    }

    @Test
    void encrypt_producesDifferentCiphertextEachTime_dueToRandomIv() {
        CredentialEncryptor encryptor = new CredentialEncryptor(VALID_KEY);

        String first = encryptor.encrypt("same-plaintext");
        String second = encryptor.encrypt("same-plaintext");

        assertThat(first).isNotEqualTo(second);
        assertThat(encryptor.decrypt(first)).isEqualTo("same-plaintext");
        assertThat(encryptor.decrypt(second)).isEqualTo("same-plaintext");
    }

    @Test
    void encrypt_withMissingKey_failsSafely() {
        CredentialEncryptor encryptor = new CredentialEncryptor("");

        assertThatThrownBy(() -> encryptor.encrypt("anything"))
                .isInstanceOf(CredentialEncryptionException.class)
                .hasMessageContaining("not configured");
    }

    @Test
    void decrypt_withMissingKey_failsSafely() {
        CredentialEncryptor encryptor = new CredentialEncryptor(null);

        assertThatThrownBy(() -> encryptor.decrypt("dG90YWxseS1lbmNyeXB0ZWQ="))
                .isInstanceOf(CredentialEncryptionException.class)
                .hasMessageContaining("not configured");
    }

    @Test
    void encrypt_withMalformedBase64Key_failsSafely() {
        CredentialEncryptor encryptor = new CredentialEncryptor("not-valid-base64!!!###");

        assertThatThrownBy(() -> encryptor.encrypt("anything"))
                .isInstanceOf(CredentialEncryptionException.class)
                .hasMessageContaining("not valid Base64");
    }

    @Test
    void encrypt_withWrongSizeKey_failsSafely() {
        // Valid base64, but only 16 bytes (AES-128 size) — this service requires exactly 32.
        CredentialEncryptor encryptor = new CredentialEncryptor("MTIzNDU2Nzg5MDEyMzQ1Ng==");

        assertThatThrownBy(() -> encryptor.encrypt("anything"))
                .isInstanceOf(CredentialEncryptionException.class)
                .hasMessageContaining("32 bytes");
    }

    @Test
    void decrypt_withCorruptedCiphertext_failsSafely() {
        CredentialEncryptor encryptor = new CredentialEncryptor(VALID_KEY);
        String encrypted = encryptor.encrypt("sk-super-secret-value");
        String corrupted = encrypted.substring(0, encrypted.length() - 4) + "abcd";

        assertThatThrownBy(() -> encryptor.decrypt(corrupted))
                .isInstanceOf(CredentialEncryptionException.class);
    }

    @Test
    void decrypt_withNonBase64Garbage_failsSafely() {
        CredentialEncryptor encryptor = new CredentialEncryptor(VALID_KEY);

        assertThatThrownBy(() -> encryptor.decrypt("not-base64-at-all!!!"))
                .isInstanceOf(CredentialEncryptionException.class);
    }

    @Test
    void encryptAndDecrypt_handleNullAsNull() {
        CredentialEncryptor encryptor = new CredentialEncryptor(VALID_KEY);

        assertThat(encryptor.encrypt(null)).isNull();
        assertThat(encryptor.decrypt(null)).isNull();
    }
}
