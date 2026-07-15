# PLAN: S-Semi 반도체 시료 생산주문관리 시스템 구현 계획

> 참고 문서: [PRD.md](PRD.md), [features/](features/00-overview.md)
> 각 기능은 [tdd 스킬](../.claude/skills/tdd/SKILL.md)에 따라 RED → Green → Refactor 순서로
> 구현하며, 단계마다 커밋을 나누고 사용자 컨펌 후 다음 단계로 진행한다.

## 진행 상황 요약

| Phase | 내용 | 상태 |
|---|---|---|
| 0 | 프로젝트 기반 구조 설정 | ✅ 완료 |
| 1 | 시료 관리 (등록/조회/검색) | ✅ 완료 |
| 2 | 시료 주문 접수 (예약) | ✅ 완료 |
| 3 | 주문 승인/거절 | ✅ 완료 |
| 4 | 생산 라인 (FIFO 생산 큐) | 🔧 진행중 |
| 5 | 모니터링 | ☐ 미착수 |
| 6 | 출고 처리 | ☐ 미착수 |
| 7 | 메인 메뉴 통합 | ☐ 미착수 |
| 8 | 마무리 (정합성 점검/회귀 테스트) | ☐ 미착수 |

상태 표기: ☐ 미착수 / 🔧 진행중 / ✅ 완료

---

## Phase 0. 프로젝트 기반 구조 설정

**목표**: 이후 모든 기능이 의존하는 도메인 모델·영속성·CLI 뼈대를 준비한다.

디렉토리 구조는 아래로 확정 (PoC 저장소 ConsoleMVC, DataPersistence 참고):
```
src/
  domain/        # Sample, Order, OrderStatus(Enum) 등 도메인 모델
  storage/       # JsonStorage (JSON 파일 저장, tmp+replace 원자적 쓰기)
  repository/    # SampleRepository, OrderRepository
  controller/    # 메뉴별 컨트롤러
  view/          # 콘솔 입출력
main.py
tests/
```

**PoC 검토 결과 및 채택 여부**

| 저장소 | 검토 내용 | 채택 여부 |
|---|---|---|
| ConsoleMVC | `model/` `view/` `controller/` 계층 분리, `main.py`에서 Controller가 Model+View를 조립해 `run()` 호출하는 구조 | 채택 — `src/controller`, `src/view` 계층 구조와 `main.py` 진입점 방식에 그대로 반영 (모델 계층은 `model` 대신 도메인 용어에 맞춰 `domain`으로 명명) |
| DataPersistence | `JsonStorage`: tmp 파일에 쓴 뒤 `os.replace`로 원자적 저장, 저장 시점마다 파일 전체를 JSON으로 덮어씀 | 채택 — `src/storage`의 JsonStorage 저장 방식(tmp+replace)으로 그대로 반영 |
| DataPersistence | `FileLock`으로 스레드/프로세스 간 상호배제 보장 | 미채택 — 본 시스템은 단일 프로세스 콘솔 앱으로 동시 접근이 없어 불필요한 복잡도로 판단, 생략 |
| DataPersistence | `Repository`가 dict 기반 CRUD(create/read_all/read_one/update/delete)를 수행하고 모델의 `to_dict`/`from_dict`로 변환 | 채택 — `SampleRepository`/`OrderRepository` 설계에 동일 패턴 적용 예정 (세부 항목 3) |
| DataMonitor, DummyDataGenerator | 각각 데이터 모니터링 Tool, Dummy 데이터 생성 Tool로 확인만 하고 상세 코드는 미검토 | 이번 Phase 0 범위에서는 미채택 — 필요 시 이후 Phase(모니터링/테스트 데이터 준비)에서 재검토 |

**세부 진행 항목**

1. ✅ `src/domain` 도메인 모델 정의: `Sample`, `OrderStatus`(Enum), `Order` (순수 데이터
   클래스, 비즈니스 로직 없음)
2. ✅ `src/storage` JsonStorage 구현 (JSON 파일 저장, tmp+replace 원자적 쓰기; FileLock 등
   파일 락은 단일 프로세스 콘솔 앱이라 미채택)
3. ✅ `src/repository` SampleRepository, OrderRepository 구현 (dict 기반 CRUD, 모델의
   to_dict/from_dict 변환 활용)
4. ✅ 콘솔 앱 진입점(`main.py`) 및 최소한의 메뉴 루프 스켈레톤 (`ConsoleView` + `MainController`,
   메뉴 0~6 표시, 0 입력 시 종료, 1~6은 "아직 구현되지 않은 기능" 안내, 하위 메뉴는 이후
   Phase에서 채움)

**참고 문서**: [00-overview.md](features/00-overview.md)

---

## Phase 1. 시료 관리 (등록/조회/검색)

**목표**: 시료 등록·조회·검색 기능 구현. 이후 모든 주문 관련 기능의 전제 조건.

- 시료 등록: 시료 ID(고유), 이름, 평균 생산시간, 수율 입력받아 등록 (초기 재고 0)
- 시료 ID 중복 검증
- 시료 목록 조회: 재고 수량 포함, 5개 단위 pagination + 하단 페이지 정보 표시
- 시료 검색: 이름 등 속성 기반 검색
- 등록되지 않은 시료는 이후 주문 불가하다는 규칙을 위한 조회 API 제공

**세부 진행 항목**

1. ✅ 시료 등록 기능 — `SampleController`가 view로부터 시료 ID/이름/평균 생산시간/수율을
   입력받아 `SampleRepository.create`로 등록. 중복 ID면 오류 안내 메시지, 성공하면 성공
   메시지 출력 (재고는 입력받지 않고 항상 0으로 시작)
2. ✅ 시료 목록 조회 — 재고 수량 포함, 5개씩 pagination + 하단 페이지 정보 표시 (페이지
   이동 입력 UI는 항목 4에서 메뉴 연결과 함께 추가 예정)
3. ✅ 시료 검색 — 이름 등 속성 기반 검색 (부분 일치)
4. ✅ 메인 메뉴(1번)에 시료 관리 서브메뉴 연결 (MainController에서 "1" 입력 시 시료 관리
   서브메뉴로 진입, 등록/조회(페이지 이동 포함)/검색/뒤로가기 라우팅)

**참고 문서**: [01-sample-management.md](features/01-sample-management.md)

---

## Phase 2. 시료 주문 접수 (예약)

**목표**: 고객 주문을 `RESERVED` 상태로 접수한다.

- 주문 입력: 시료 ID, 고객명, 주문 수량
- 등록되지 않은 시료 ID 주문 시 거부 처리
- 주문번호 발급 (예: `ORD-YYYYMMDD-NNNN`)
- 주문 상태 `RESERVED`로 등록, 이 시점에는 재고 검증/차감 없음

**세부 진행 항목**

1. ✅ 주문 접수 기능 — `OrderController`(신규)가 view로부터 시료 ID/고객명/주문 수량을
   입력받아 주문을 생성. 등록되지 않은 시료 ID면 거부(오류 안내), 유효하면
   `ORD-YYYYMMDD-NNNN` 형식으로 주문번호를 채번하고 `OrderRepository.create`로 `RESERVED`
   상태 주문 등록
2. ✅ 메인 메뉴(2번)에 시료 주문 서브메뉴 연결 (MainController에서 "2" 입력 시 시료 주문
   서브메뉴로 진입, 접수/뒤로가기 라우팅 — 이번 Phase 범위는 접수 기능만)

**참고 문서**: [02-order-reservation.md](features/02-order-reservation.md)

---

## Phase 3. 주문 승인/거절

**목표**: `RESERVED` 주문을 검토하여 승인/거절 처리하고, 승인 시 재고 상황에 따라 분기한다.

- 접수된(`RESERVED`) 주문 목록 표시
- 거절 처리: `RESERVED` → `REJECTED`, 이후 프로세스 미진행
- 승인 처리 분기:
  - 재고 충분(주문 수량 ≤ 재고): `RESERVED` → `CONFIRMED`
  - 재고 부족(주문 수량 > 재고): `RESERVED` → `PRODUCING`, 생산 큐에 등록 (Phase 4 연계)
- 승인/거절 대상이 `RESERVED`가 아닌 경우 처리 불가 검증

**세부 진행 항목**

1. ✅ 접수된 주문 목록 표시 — `OrderController`가 `RESERVED` 상태의 주문만 필터링해 view를
   통해 출력 (pagination 없이 전체 표시), 없으면 안내 메시지
2. ✅ 주문 승인 처리 — 재고 충분/부족에 따라 `CONFIRMED`/`PRODUCING`으로 분기 (이번 Phase에서는
   상태 전환만 다루고, FIFO 생산 큐 처리는 Phase 4에서 추가)
3. ✅ 주문 거절 처리 — `RESERVED` → `REJECTED`
4. ✅ 메인 메뉴(3번)에 주문 승인/거절 서브메뉴 연결 (`OrderController.run_approval_submenu()`,
   "2"번 접수 서브메뉴 `run_submenu()`와는 별개). UX 개선: 주문번호(`ORD-YYYYMMDD-NNNN`)를
   직접 타이핑하는 대신, 서브메뉴 루프마다 `RESERVED` 주문 목록을 번호(1, 2, 3…)와 함께
   자동으로 보여주고, 승인/거절 시 그 번호로 선택하게 한다 (메뉴는 "1.승인/2.거절/0.뒤로가기").

**참고 문서**: [03-order-approval.md](features/03-order-approval.md)

---

## Phase 4. 생산 라인 (FIFO 생산 큐)

**목표**: 단일 생산 라인 + FIFO 큐로 부족분을 생산하고, 완료 시 재고에 반영한다.

- 생산량 계산 로직: 부족분 = 주문량 - 승인 시점 재고, 실생산량 = `ceil(부족분 / 수율)`,
  총 생산 시간 = 평균 생산시간 × 실생산량
- 생산 큐 등록 (FIFO, 새치기 불가) 및 단일 라인 동시 처리 제한
- 실시간 대기 방식 처리 (총 생산 시간 경과 후 완료 처리 — 테스트 시 시간 mocking 필요,
  pytest-mock 활용)
- 생산 완료 시: 실생산량 전량 재고 반영 + 주문 상태 `PRODUCING` → `CONFIRMED` + 큐의 다음
  주문 이어서 생산
- 생산 현황 조회(진행 중인 주문 정보) / 대기 큐 목록(FIFO 순서) 조회

**아키텍처 결정**
- "실시간 대기"는 백그라운드 스레드가 아니라, 생산라인 관련 메뉴 진입 시점에 경과 시간을
  확인해서 완료 처리하는 방식(lazy/on-demand check)으로 구현한다.
- FIFO 큐는 `Order` 모델을 건드리지 않고, 신규 저장소(`ProductionQueueRepository` + JSON
  storage)로 별도 관리한다. 이 저장소는 JSON 리스트에 append된 순서 = FIFO 순서로 취급한다
  (별도 정렬 불필요).

**세부 진행 항목**

1. ✅ 생산 큐 도메인 모델 및 저장소 — `ProductionJob`(순수 데이터클래스)과
   `ProductionQueueRepository`(CRUD) 신규 구현
2. ✅ 주문 승인 시 생산 큐 등록 연동 — `OrderController.approve()`에서 PRODUCING 분기 시
   생산량 계산(부족분/실생산량/총생산시간) 후 `ProductionJob`을 큐에 등록. 큐가 비어있었으면
   즉시 시작(`started_at` 기록), 아니면 대기(`started_at=None`)
3. ✅ 생산 라인 진행 확인 로직 — 큐의 선두 작업이 완료 시간을 지났으면 재고 반영 + 주문 상태
   `PRODUCING`→`CONFIRMED` + 큐에서 제거 + 다음 작업 시작 처리 (여러 개가 동시에 완료 시간을
   지났을 수도 있으니 반복 처리)
4. ✅ 생산 현황 조회 / 대기 큐 목록 확인 (메뉴 5의 하위 기능)
5. ✅ 메인 메뉴(5번)에 생산 라인 서브메뉴 연결 (진입 시 3번의 진행 확인 로직을 먼저 실행)

**참고 문서**: [05-production-line.md](features/05-production-line.md)

---

## Phase 5. 모니터링

**목표**: 상태별 주문 현황과 시료별 재고 상태를 집계해 보여준다.

- 상태별(`RESERVED`/`CONFIRMED`/`PRODUCING`/`RELEASE`) 주문 건수 집계 (`REJECTED` 제외)
- 시료별 필요 수량 산출: 해당 시료의 `RESERVED` 주문 수량 합
- 재고 상태 판정: 고갈(재고==0) / 부족(0<재고<필요수량) / 여유(재고>0 and 재고>=필요수량)
- `RESERVED` 주문이 없는 시료는 필요 수량 0으로 간주

**참고 문서**: [04-monitoring.md](features/04-monitoring.md)

---

## Phase 6. 출고 처리

**목표**: `CONFIRMED` 주문을 출고 처리하여 `RELEASE`로 전환한다.

- `CONFIRMED` 상태 주문 목록 표시
- 특정 주문 선택 후 출고 실행 → 상태 `CONFIRMED` → `RELEASE`
- `CONFIRMED`가 아닌 주문에 대한 출고 시도 차단
- `RELEASE`는 최종 상태로 이후 전이 불가 검증

**참고 문서**: [06-shipment.md](features/06-shipment.md)

---

## Phase 7. 메인 메뉴 통합

**목표**: 개별로 구현한 기능들을 메인 메뉴에서 하나의 콘솔 앱으로 통합한다.

- 메인 화면: 시스템 현재 시각, 등록 시료 종수/총 재고 수량, 전체 주문 건수, 생산 라인
  대기 건수 표시
- 메뉴 1~6 + 0(종료) 라우팅 연결 (Phase 1~6 기능 연동)
- 콘솔 출력 가독성 개선: 각 Phase에서 개별적으로 만든 메뉴/목록/검색 결과 출력 형식을
  일관된 스타일(구분선, 표 형태 정렬 등)로 다듬는다 (docs/features/00-overview.md 참고 —
  화면 구성은 자유롭게 결정 가능)
- 사용자 역할(주문 담당자/생산 담당자) 관점에서 전체 플로우 수동 점검

**참고 문서**: [00-overview.md](features/00-overview.md)

---

## Phase 8. 마무리

**목표**: 전체 기능의 문서-코드 정합성과 회귀 테스트를 확인하고 마무리한다.

- `doc-consistency-verifier` 서브에이전트로 PRD/기능 문서 vs 구현 정합성 검증
- `test-verifier` 서브에이전트로 전체 테스트 스위트 실행 및 결과 확인
- 상태 전이 다이어그램(PRD 6장) 기준 End-to-End 시나리오 수동 점검
  (RESERVED → 승인/거절 → (PRODUCING →) CONFIRMED → RELEASE)

---

## 진행 방식 메모

- Phase는 순서대로 진행하되, 상위 Phase가 하위 Phase의 도메인 모델/저장소를 전제로 하므로
  순서를 크게 벗어나지 않는다.
- 각 Phase 내 기능 단위로 RED/Green/Refactor 커밋을 반복한다. RED 단계마다 해당 요구사항을
  이 파일에 작성/갱신하며, Phase의 모든 요구사항 구현이 끝나면 상단 진행 상황 요약의 Phase
  상태(☐/🔧/✅)를 갱신한다.
- 진행 중 PRD/기능 문서와 어긋나는 결정이 필요하면 먼저 문서를 갱신한 뒤 구현한다.
