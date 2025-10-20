package com.mommyshops.auth.domain;

import java.time.OffsetDateTime;
import java.util.UUID;

import jakarta.persistence.Column;
import jakarta.persistence.ElementCollection;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "user_accounts")
public class UserAccount {

	@Id
	private UUID id;

	@Column(nullable = false, unique = true)
	private String email;

	@Column(nullable = false)
	private String fullName;

	@Column(nullable = false)
	private String googleSub;

	@Column(nullable = false)
	private OffsetDateTime createdAt;

	@ElementCollection(fetch = FetchType.EAGER)
	private java.util.Set<String> roles;

	@Column(nullable = false)
	private boolean tutorialCompleted;

	@Column
	private String picture;

	@Column
	private String provider;

	@Column
	private String providerId;

	@Column
	private OffsetDateTime lastLoginAt;

	@Column(nullable = false)
	private boolean active = true;

	protected UserAccount() {
	}

	public UserAccount(UUID id, String email, String fullName, String googleSub, OffsetDateTime createdAt,
		java.util.Set<String> roles, boolean tutorialCompleted) {
		this.id = id;
		this.email = email;
		this.fullName = fullName;
		this.googleSub = googleSub;
		this.createdAt = createdAt;
		this.roles = roles;
		this.tutorialCompleted = tutorialCompleted;
	}

	public UserAccount(UUID id, String email, String fullName, String googleSub, OffsetDateTime createdAt,
		java.util.Set<String> roles, boolean tutorialCompleted, String picture, String provider, 
		String providerId, OffsetDateTime lastLoginAt, boolean active) {
		this.id = id;
		this.email = email;
		this.fullName = fullName;
		this.googleSub = googleSub;
		this.createdAt = createdAt;
		this.roles = roles;
		this.tutorialCompleted = tutorialCompleted;
		this.picture = picture;
		this.provider = provider;
		this.providerId = providerId;
		this.lastLoginAt = lastLoginAt;
		this.active = active;
	}

	public UUID getId() {
		return id;
	}

	public String getEmail() {
		return email;
	}

	public String getFullName() {
		return fullName;
	}

	public String getGoogleSub() {
		return googleSub;
	}

	public OffsetDateTime getCreatedAt() {
		return createdAt;
	}

	public java.util.Set<String> getRoles() {
		return roles;
	}

	public boolean isTutorialCompleted() {
		return tutorialCompleted;
	}

	public void completeTutorial() {
		this.tutorialCompleted = true;
	}

	// Additional getters and setters
	public void setId(UUID id) {
		this.id = id;
	}

	public void setEmail(String email) {
		this.email = email;
	}

	public void setName(String name) {
		this.fullName = name;
	}

	public String getName() {
		return this.fullName;
	}

	public void setPicture(String picture) {
		this.picture = picture;
	}

	public String getPicture() {
		return picture;
	}

	public void setProvider(String provider) {
		this.provider = provider;
	}

	public String getProvider() {
		return provider;
	}

	public void setProviderId(String providerId) {
		this.providerId = providerId;
	}

	public String getProviderId() {
		return providerId;
	}

	public void setCreatedAt(OffsetDateTime createdAt) {
		this.createdAt = createdAt;
	}

	public void setLastLoginAt(OffsetDateTime lastLoginAt) {
		this.lastLoginAt = lastLoginAt;
	}

	public OffsetDateTime getLastLoginAt() {
		return lastLoginAt;
	}

	public void setActive(boolean active) {
		this.active = active;
	}

	public boolean isActive() {
		return active;
	}

	public void setRoles(java.util.Set<String> roles) {
		this.roles = roles;
	}

	public void setTutorialCompleted(boolean tutorialCompleted) {
		this.tutorialCompleted = tutorialCompleted;
	}
}
