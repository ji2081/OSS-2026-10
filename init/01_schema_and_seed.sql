-- ============================================================
-- Youth Policy Optimizer — Schema & Seed
-- Single-table design: policies (MWIS 노드 + 간선 통합)
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 기존 테이블 드롭 (재실행 안전)
DROP TABLE IF EXISTS etl_logs CASCADE;
DROP TABLE IF EXISTS result_policies CASCADE;
DROP TABLE IF EXISTS optimization_results CASCADE;
DROP TABLE IF EXISTS user_profiles CASCADE;
DROP TABLE IF EXISTS policy_exclusions CASCADE;
DROP TABLE IF EXISTS policy_details CASCADE;
DROP TABLE IF EXISTS policies CASCADE;

-- ============================================================
-- 1. policies — 핵심 단일 테이블
-- ============================================================
CREATE TABLE policies (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_id       VARCHAR(50)     UNIQUE NOT NULL,
    title           VARCHAR(255)    NOT NULL,
    category        VARCHAR(20)     NOT NULL CHECK (category IN ('employment','housing','finance','life')),
    super_region    VARCHAR(50)     NOT NULL,
    sub_region      VARCHAR(50)     NOT NULL,
    age_min         INTEGER         NOT NULL,
    age_max         INTEGER         NOT NULL,
    income_standard VARCHAR(20),
    income_limit    INTEGER,
    benefit_type    VARCHAR(20)     NOT NULL,
    total_benefit   BIGINT          NOT NULL,
    apply_start     TIMESTAMP,
    apply_end       TIMESTAMP,
    exclusive_with  JSONB           NOT NULL DEFAULT '[]',
    raw_data        JSONB           NOT NULL DEFAULT '{}',
    updated_at      TIMESTAMP       NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_age CHECK (age_min <= age_max)
);

CREATE INDEX idx_policies_category     ON policies (category);
CREATE INDEX idx_policies_region       ON policies (super_region, sub_region);
CREATE INDEX idx_policies_age          ON policies (age_min, age_max);
CREATE INDEX idx_policies_exclusive    ON policies USING GIN (exclusive_with);

-- ============================================================
-- 2. user_profiles — 사용자 프로필
-- ============================================================
CREATE TABLE user_profiles (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    age             INTEGER         NOT NULL,
    income_level    INTEGER,
    region          VARCHAR(50)     NOT NULL,
    sub_region      VARCHAR(50)     DEFAULT '전체',
    is_employed     BOOLEAN         DEFAULT FALSE,
    created_at      TIMESTAMP       DEFAULT NOW()
);

-- ============================================================
-- 3. optimization_results — MWIS 실행 결과
-- ============================================================
CREATE TABLE optimization_results (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID            REFERENCES user_profiles(id) ON DELETE CASCADE,
    total_benefit   BIGINT          NOT NULL,
    policy_count    INTEGER         NOT NULL,
    algorithm       VARCHAR(30)     DEFAULT 'mwis_dfs_dp',
    exec_ms         INTEGER,
    created_at      TIMESTAMP       DEFAULT NOW()
);

-- ============================================================
-- 4. result_policies — 결과 ↔ 정책 매핑
-- ============================================================
CREATE TABLE result_policies (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    result_id       UUID            REFERENCES optimization_results(id) ON DELETE CASCADE,
    policy_id       VARCHAR(50)     REFERENCES policies(policy_id) ON DELETE CASCADE,
    seq_order       INTEGER         NOT NULL,
    start_date      DATE,
    end_date        DATE
);

-- ============================================================
-- 5. etl_logs — ETL 파이프라인 로그
-- ============================================================
CREATE TABLE etl_logs (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    source          VARCHAR(100)    NOT NULL,
    status          VARCHAR(20)     NOT NULL CHECK (status IN ('success','fail','partial')),
    records_in      INTEGER         DEFAULT 0,
    records_out     INTEGER         DEFAULT 0,
    confidence_avg  NUMERIC(4,2),
    error_msg       TEXT,
    created_at      TIMESTAMP       DEFAULT NOW()
);

-- ============================================================
-- SEED DATA — 22개 MVP 정책
-- ============================================================
INSERT INTO policies (policy_id, title, category, super_region, sub_region, age_min, age_max, income_standard, income_limit, benefit_type, total_benefit, apply_start, apply_end, exclusive_with, raw_data) VALUES

-- [부동산] 9개
('MOLIT_RENT_01',
 '국토교통부 청년월세 한시 특별지원',
 'housing', '전국', '전체', 19, 34,
 'median', 60,
 'monthly_cash', 2400000,
 '2024-02-26', '2025-12-31',
 '["SEOUL_RENT_01"]',
 '{"monthly_amount":200000,"duration_months":12,"note":"월 20만원×12개월, 서울시 청년월세지원과 중복 불가"}'
),

('SEOUL_RENT_01',
 '서울시 청년월세지원',
 'housing', '서울', '전체', 19, 39,
 'median', 150,
 'monthly_cash', 2400000,
 '2024-03-01', '2025-12-31',
 '["MOLIT_RENT_01"]',
 '{"monthly_amount":200000,"duration_months":12,"note":"월 20만원×12개월, 국토부 청년월세와 중복 불가"}'
),

('SME_DEPOSIT_01',
 '중소기업취업청년 전월세보증금 대출',
 'housing', '전국', '전체', 19, 34,
 'salary', 35000000,
 'loan', 100000000,
 NULL, NULL,
 '[]',
 '{"loan_limit":100000000,"interest_rate":1.2,"duration_years":2,"extension":4,"note":"연 1.2%, 최대 1억원"}'
),

('JEONSE_LOAN_01',
 '청년 버팀목 전세자금대출',
 'housing', '전국', '전체', 19, 34,
 'median', 100,
 'loan', 70000000,
 NULL, NULL,
 '["SME_DEPOSIT_01"]',
 '{"loan_limit":70000000,"interest_rate":1.8,"duration_years":2,"extension":4,"note":"연 1.8%, 전월세보증금 대출과 중복 주의"}'
),

('SEOUL_DEPOSIT_INT_01',
 '서울시 청년 임차보증금 이자지원',
 'housing', '서울', '전체', 19, 39,
 'median', 100,
 'interest_subsidy', 1200000,
 '2024-01-01', '2025-12-31',
 '[]',
 '{"annual_subsidy":600000,"duration_years":2,"note":"연 최대 60만원×2년"}'
),

('MONTHLY_LOAN_01',
 '청년전용 보증부월세 대출',
 'housing', '전국', '전체', 19, 34,
 'median', 100,
 'loan', 12000000,
 NULL, NULL,
 '[]',
 '{"deposit_limit":37000000,"monthly_limit":400000,"duration_months":30,"interest_rate":1.3,"note":"보증금+월세 대출 패키지"}'
),

('SEOUL_MOVING_01',
 '1인가구 청년 부동산 중개보수 및 이사비 지원',
 'housing', '서울', '전체', 19, 39,
 'median', 150,
 'one_time_cash', 510000,
 '2024-03-01', '2024-12-31',
 '[]',
 '{"broker_fee":310000,"moving_fee":200000,"note":"중개보수 31만+이사비 20만, 1회성"}'
),

('SEOUL_SAFETY_01',
 '청년 1인가구 안심장비 지원 사업',
 'life', '서울', '전체', 19, 39,
 'median', 100,
 'goods', 160000,
 '2024-04-01', '2024-12-31',
 '[]',
 '{"items":"스마트초인종, 창문잠금장치 등","value":160000,"note":"안심장비 키트 지원"}'
),

('DREAM_SAVINGS_01',
 '청년주택드림청약통장 및 연계 대출',
 'housing', '전국', '전체', 19, 34,
 'salary', 50000000,
 'savings_interest', 6000000,
 NULL, NULL,
 '[]',
 '{"monthly_deposit_max":1000000,"interest_rate":4.5,"duration_years":2,"note":"최대 4.5% 우대금리, 청약 연계"}'
),

-- [자산형성/금융] 7개
('SEOUL_HOPE_01',
 '희망두배청년통장',
 'finance', '서울', '전체', 18, 34,
 'median', 100,
 'savings_match', 6000000,
 '2024-05-01', '2024-06-30',
 '["TOMORROW_SAVE_01"]',
 '{"monthly_save":150000,"match_ratio":"1:1","duration_months":24,"total_match":3600000,"note":"본인 월 15만원 저축 → 시 매칭 15만원×24개월"}'
),

('TOMORROW_SAVE_01',
 '청년 내일 저축계좌',
 'finance', '전국', '전체', 15, 39,
 'median', 100,
 'savings_match', 7200000,
 NULL, NULL,
 '["SEOUL_HOPE_01"]',
 '{"monthly_save":100000,"gov_match":300000,"duration_months":36,"note":"본인 10만+정부 30만×36개월, 희망두배와 중복 불가"}'
),

('SEOUL_STUDENT_LOAN_01',
 '서울시 대학생 학자금 대출 이자지원',
 'finance', '서울', '전체', 18, 34,
 'median', 150,
 'interest_subsidy', 2000000,
 '2024-03-01', '2024-12-31',
 '[]',
 '{"annual_max":1000000,"duration_years":2,"note":"연 최대 100만원×2년"}'
),

('FUTURE_SAVINGS_01',
 '청년 미래 적금',
 'finance', '전국', '전체', 19, 34,
 'salary', 50000000,
 'savings_interest', 3600000,
 NULL, NULL,
 '[]',
 '{"monthly_max":500000,"bonus_rate":6.0,"duration_months":12,"note":"신규 예정, 6% 우대금리"}'
),

('MILITARY_SAVINGS_01',
 '장병내일준비적금',
 'finance', '전국', '전체', 18, 30,
 NULL, NULL,
 'savings_match', 10200000,
 NULL, NULL,
 '[]',
 '{"monthly_max":400000,"match_ratio":"33%","interest_rate":5.0,"duration_months":18,"note":"복무 중 적금, 정부 매칭 33%+5% 금리"}'
),

('KPASS_01',
 '청년 K-패스',
 'life', '전국', '전체', 19, 34,
 NULL, NULL,
 'cashback', 561600,
 NULL, NULL,
 '["CLIMATE_CARD_01"]',
 '{"monthly_cashback":46800,"duration_months":12,"cashback_rate":"30%","note":"대중교통 30% 환급, 기후동행카드와 중복 불가"}'
),

('CLIMATE_CARD_01',
 '기후동행카드',
 'life', '서울', '전체', 0, 99,
 NULL, NULL,
 'discount', 468000,
 NULL, NULL,
 '["KPASS_01"]',
 '{"monthly_fee":65000,"market_equivalent":104000,"monthly_savings":39000,"duration_months":12,"note":"월 6.5만원 정액제, 월 약 3.9만원 절감 추정"}'
),

-- [취업/교육/생활] 6개
('EXAM_FEE_01',
 '미취업 청년 어학·자격증 응시료 지원',
 'employment', '전국', '전체', 18, 34,
 'median', 200,
 'one_time_cash', 500000,
 '2024-01-01', '2024-12-31',
 '[]',
 '{"max_per_year":500000,"items":"TOEIC, 한능검, 기사 등","note":"연 최대 50만원"}'
),

('SEOUL_ALLOWANCE_01',
 '서울 청년수당',
 'employment', '서울', '전체', 19, 34,
 'median', 150,
 'monthly_cash', 3000000,
 '2024-03-01', '2024-12-31',
 '["NES_01"]',
 '{"monthly_amount":500000,"duration_months":6,"note":"월 50만원×6개월, 국민취업지원제도와 중복 불가"}'
),

('CERT_FEE_01',
 '청년 국가기술자격시험 응시료 지원사업',
 'employment', '전국', '전체', 18, 34,
 NULL, NULL,
 'one_time_cash', 200000,
 '2024-01-01', '2024-12-31',
 '[]',
 '{"max_per_year":200000,"note":"국가기술자격 응시료 한정"}'
),

('SEOUL_EDU_VOUCHER_01',
 '서울시 평생교육이용권',
 'life', '서울', '전체', 19, 64,
 'median', 170,
 'voucher', 350000,
 '2024-01-01', '2024-12-31',
 '[]',
 '{"amount":350000,"note":"1인 1회 35만원 바우처"}'
),

('EITC_01',
 '근로장려금',
 'finance', '전국', '전체', 19, 99,
 'salary', 22000000,
 'annual_cash', 1650000,
 NULL, NULL,
 '[]',
 '{"single_max":1650000,"note":"단독 가구 기준 최대 165만원, 소득에 따라 차등"}'
),

('NES_01',
 '국민취업지원제도',
 'employment', '전국', '전체', 15, 69,
 'median', 120,
 'monthly_cash', 3600000,
 NULL, NULL,
 '["SEOUL_ALLOWANCE_01"]',
 '{"monthly_amount":500000,"duration_months":6,"note":"1유형 구직촉진수당 월 50만×6개월, 서울청년수당과 중복 불가"}'
);

-- ============================================================
-- 검증 쿼리
-- ============================================================
DO $$
DECLARE
    cnt INTEGER;
BEGIN
    SELECT COUNT(*) INTO cnt FROM policies;
    IF cnt <> 22 THEN
        RAISE EXCEPTION 'Expected 22 policies, got %', cnt;
    END IF;
    RAISE NOTICE '✅ Seed verification passed: % policies loaded', cnt;
END $$;
