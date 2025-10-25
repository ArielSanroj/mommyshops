package com.mommyshops.integration.domain;

import java.time.OffsetDateTime;
import java.util.UUID;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "external_source_log")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
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
}
