package com.mommyshops;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

@SpringBootApplication
@EnableJpaRepositories(basePackages = "com.mommyshops")
@EntityScan(basePackages = "com.mommyshops")
public class MommyshopsApplication {

	public static void main(String[] args) {
		SpringApplication.run(MommyshopsApplication.class, args);
	}
}
