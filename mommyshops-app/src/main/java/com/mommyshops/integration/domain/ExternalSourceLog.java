package com.mommyshops.integration.domain;

import java.time.OffsetDateTime;
import java.util.UUID;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "external_source_log")
public class ExternalSourceLog {

	@Id
	private UUID id;

	@Column(nullable = false)
	private String sourceName;

	@Column(nullable = false)
	private String query;

	@Column(columnDefinition = "TEXT")
	private String responseSummary;

	@Column(nullable = false)
	private OffsetDateTime fetchedAt;

	@Column(nullable = false)
	private int statusCode;

	protected ExternalSourceLog() {
	}

	public ExternalSourceLog(UUID id, String sourceName, String query, String responseSummary, OffsetDateTime fetchedAt,
		int statusCode) {
		this.id = id;
		this.sourceName = sourceName;
		this.query = query;
		this.responseSummary = responseSummary;
		this.fetchedAt = fetchedAt;
		this.statusCode = statusCode;
	}

	public UUID getId() {
		return id;
	}

	public String getSourceName() {
		return sourceName;
	}

	public String getQuery() {
		return query;
	}

	public String getResponseSummary() {
		return responseSummary;
	}

	public OffsetDateTime getFetchedAt() {
		return fetchedAt;
	}

	public int getStatusCode() {
		return statusCode;
	}
}
