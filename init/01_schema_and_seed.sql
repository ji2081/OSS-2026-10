CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

DROP TABLE IF EXISTS etl_logs CASCADE;
DROP TABLE IF EXISTS result_policies CASCADE;
DROP TABLE IF EXISTS optimization_results CASCADE;
DROP TABLE IF EXISTS user_profiles CASCADE;
DROP TABLE IF EXISTS policies CASCADE;

CREATE TABLE policies (
    id                      UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    title                   VARCHAR(255)    NOT NULL UNIQUE,
    category                VARCHAR(20)     NOT NULL CHECK (category IN (
                                'housing','finance','employment',
                                'education','health','culture','welfare','startup'
                            )),
    benefit_type            VARCHAR(20)     NOT NULL CHECK (benefit_type IN (
                                'subsidy','loan','savings','voucher',
                                'interest_subsidy','goods','cashback','pass','other'
                            )),
    host_org                VARCHAR(100),
    super_region            VARCHAR(50)     NOT NULL DEFAULT '전국',
    sub_region              VARCHAR(50),
    age_min                 INTEGER,
    age_max                 INTEGER,
    income_standard         FLOAT,
    income_limit            INTEGER,
    total_benefit           BIGINT,
    benefit_duration_months INTEGER,
    benefit_description     TEXT,
    apply_start             DATE,
    apply_end               DATE,
    is_active               BOOLEAN         NOT NULL DEFAULT TRUE,
    target_unemployed_only  BOOLEAN         NOT NULL DEFAULT FALSE,
    exclusive_with          JSONB           NOT NULL DEFAULT '[]',
    source_url              VARCHAR(500),
    confidence              FLOAT           DEFAULT 1.0,
    raw_data                TEXT,
    updated_at              TIMESTAMP       NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_age CHECK (age_min IS NULL OR age_max IS NULL OR age_min <= age_max),
    CONSTRAINT chk_confidence CHECK (confidence >= 0.0 AND confidence <= 1.0)
);

CREATE INDEX idx_policies_category  ON policies (category);
CREATE INDEX idx_policies_region    ON policies (super_region, sub_region);
CREATE INDEX idx_policies_age       ON policies (age_min, age_max);
CREATE INDEX idx_policies_active    ON policies (is_active);
CREATE INDEX idx_policies_exclusive ON policies USING GIN (exclusive_with);

CREATE TABLE user_profiles (
    id           UUID      PRIMARY KEY DEFAULT uuid_generate_v4(),
    age          INTEGER   NOT NULL,
    income_level INTEGER,
    region       VARCHAR(50) NOT NULL,
    sub_region   VARCHAR(50) DEFAULT '전체',
    is_employed  BOOLEAN   DEFAULT FALSE,
    created_at   TIMESTAMP DEFAULT NOW()
);

CREATE TABLE optimization_results (
    id            UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id       UUID    REFERENCES user_profiles(id) ON DELETE CASCADE,
    total_benefit BIGINT  NOT NULL,
    policy_count  INTEGER NOT NULL,
    algorithm     VARCHAR(30) DEFAULT 'mwis_dfs_dp',
    exec_ms       INTEGER,
    created_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE result_policies (
    id         UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    result_id  UUID    REFERENCES optimization_results(id) ON DELETE CASCADE,
    policy_id  UUID    REFERENCES policies(id) ON DELETE CASCADE,
    seq_order  INTEGER NOT NULL,
    start_date DATE,
    end_date   DATE
);

CREATE TABLE etl_logs (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_at          TIMESTAMP   NOT NULL,
    source          VARCHAR(100) NOT NULL,
    total_extracted INTEGER     DEFAULT 0,
    total_inserted  INTEGER     DEFAULT 0,
    total_skipped   INTEGER     DEFAULT 0,
    total_failed    INTEGER     DEFAULT 0,
    errors          JSONB       DEFAULT '[]',
    created_at      TIMESTAMP   DEFAULT NOW()
);