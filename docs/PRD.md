# PRD: S-Semi 반도체 시료 생산주문관리 시스템

> 초안(draft) 문서입니다. 논의를 통해 계속 갱신됩니다.

## 1. 개요

S-Semi는 고객으로부터 반도체 시료(sample)를 주문받아 생산하고 납품하는 가상의 반도체회사다.
이 시스템은 시료 주문 접수부터 생산, 출고까지의 전 과정을 콘솔 환경에서 관리한다.

## 2. 사용자 역할

### 2.1 주문 담당자
- 고객의 요청을 받아 주문서를 작성한다.

### 2.2 생산 담당자
- 접수된 주문서를 검토하여 승인 또는 거절한다.
- 승인된 주문에 대해 시료 생산을 시작한다.
- 생산이 완료된 시료를 출고한다.

## 3. 주문 상태(Order Status)

| 상태 | 설명 |
|---|---|
| RESERVED | 주문 접수 상태. 주문 담당자가 주문서를 작성하면 이 상태로 등록된다. |
| REJECTED | 주문 거절 상태. 생산 담당자가 주문을 거절하면 이 상태가 된다. |
| PRODUCING | 주문 승인 완료 + 재고 부족으로 생산 중인 상태. |
| CONFIRMED | 주문 승인 완료 + 출고 대기 중인 상태. 재고가 충분해 즉시 출고 대기 상태가 되었거나, 생산이 완료되어 출고 대기 상태가 된 경우 모두 포함한다. |
| RELEASE | 출고 완료 상태. 시료가 출고되어 고객에게 납품된 상태. |

## 4. 핵심 기능

기능별 상세 명세는 [docs/features/](features/00-overview.md)에 기능 단위로 분리되어 있다.

| 기능 | 문서 |
|---|---|
| 메인 메뉴 | [00-overview.md](features/00-overview.md) |
| 시료 관리 (등록/조회/검색) | [01-sample-management.md](features/01-sample-management.md) |
| 시료 주문 (접수) | [02-order-reservation.md](features/02-order-reservation.md) |
| 주문 승인/거절 | [03-order-approval.md](features/03-order-approval.md) |
| 모니터링 | [04-monitoring.md](features/04-monitoring.md) |
| 생산 라인 | [05-production-line.md](features/05-production-line.md) |
| 출고 처리 | [06-shipment.md](features/06-shipment.md) |

### 4.1 주문서 작성 (주문 담당자)
- 주문 담당자는 신규 주문서를 작성할 수 있다.
- 작성된 주문서는 `RESERVED` 상태로 등록된다.

### 4.2 주문 승인/거절 (생산 담당자)
- 생산 담당자는 `RESERVED` 상태의 주문서를 검토하여 승인 또는 거절할 수 있다.
- 거절 시 주문 상태는 `REJECTED`로 변경되고, 이후 생산 프로세스로 진행되지 않는다.
- 승인 시 주문 대상 시료의 재고를 확인하여 아래와 같이 분기한다.
  - 재고가 충분한 경우: 생산 과정 없이 즉시 `CONFIRMED` 상태(출고 대기)로 전환한다.
  - 재고가 부족한 경우: `PRODUCING` 상태로 전환하고, 생산 대기열(생산 라인 큐)에 등록된다.

### 4.3 시료 생산 (생산 담당자)
- 생산 라인은 1개이며, 동시에 하나의 주문만 생산할 수 있다.
- 생산 대기열은 **FIFO(First-In-First-Out)** 전략을 따른다. 즉, 먼저 `PRODUCING` 상태로 전환되어
  대기열에 들어온 주문부터 순서대로 생산한다.
- 생산이 완료되면 해당 주문은 `CONFIRMED` 상태(출고 대기)로 전환되고, 생산 라인은 대기열의
  다음 주문(FIFO 순서상 가장 먼저 대기 중인 주문)을 이어서 생산한다.
- 생산량 계산: 부족분 = 주문량 - 재고, 실생산량 = `ceil(부족분 / 수율)`,
  총 생산 시간 = 평균 생산시간 × 실생산량. 자세한 내용은
  [05-production-line.md](features/05-production-line.md) 참고.

### 4.4 시료 출고 (생산 담당자)
- 생산 담당자는 `CONFIRMED` 상태의 시료를 출고할 수 있다.
- 출고 시 주문 상태는 `RELEASE`로 변경된다.

## 5. 생산 라인 정책

- 생산 라인은 **1개**만 존재한다.
- 생산 대기열은 **FIFO** 스케줄링 전략을 사용한다. `PRODUCING` 상태로 전환된 순서대로만 생산이
  진행되며, 임의로 순서를 건너뛰거나 새치기할 수 없다.

## 6. 상태 전이 요약

```
RESERVED
  ├─ 거절 → REJECTED
  └─ 승인
       ├─ 재고 충분 → CONFIRMED ─────────────────┐
       └─ 재고 부족 → PRODUCING → [생산 완료] → CONFIRMED → [출고] → RELEASE
```

## 7. 참고 PoC (구현 시 참고, 반드시 그대로 채택할 필요는 없음)

| 구분 | 저장소 |
|---|---|
| MVC 스켈레톤 코드 | https://github.com/munjeong-kim/ConsoleMVC-munjeong-12210876 |
| 데이터 영속성 처리 | https://github.com/munjeong-kim/DataPersistence-munjeong-12210876 |
| 데이터 모니터링 Tool | https://github.com/munjeong-kim/DataMonitor-munjeong-12210876 |
| Dummy 데이터 생성 Tool | https://github.com/munjeong-kim/DummyDataGenerator-munjeong-12210876 |

데이터 영속화가 필요하며, 구체적인 저장 방식(파일 포맷, 저장 위치, 저장 시점 등)은 위
"데이터 영속성 처리" PoC를 참고하여 정한다.

## 8. 미정/추후 논의 필요 사항

(현재 없음 — 거절 사유 미기록, 재고 임계값(RESERVED 주문 기준 필요 수량 대비 고갈/부족/여유),
재고 초기값(0), 생산 완료분 전량 재고 반영, 실시간 대기 방식은 모두 결정되어 각 기능 문서
([03-order-approval.md](features/03-order-approval.md), [04-monitoring.md](features/04-monitoring.md),
[05-production-line.md](features/05-production-line.md))에 반영했다.)
