@checkout @smoke
Feature: Checkout Flow
  Customers buy items and receive an order confirmation.

  Background:
    Given the user is logged in as "member"

  @happy
  Scenario: Pay with credit card
    When the user navigates to "https://shop.example.com/checkout"
    And the user fills in "4111-1111-1111-1111" into "Card Number"
    And the user clicks the "Pay Now" button
    Then the user should see "Order Confirmed"
    And the url should contain "/confirmation"

  @data-driven
  Scenario Outline: Apply voucher <voucher>
    When the user enters "<code>" into "Voucher Input"
    And the user clicks the "Apply" button
    Then the total should show "<total>"

    @valid
    Examples:
      | voucher | code   | total |
      | percent | SAVE10 | 90    |
      | fixed   | SHIP0  | 100   |

    @edge
    Examples: Boundary rows
      | voucher | code | total |
      | expired | OLD1 | 200   |

  Rule: Guest checkout restrictions

  @negative
  Scenario: Invalid card is rejected
    When the user fills in "4000-0000-0000-0002" into "Card Number"
    And the user clicks the "Pay Now" button
    Then the user should see "Payment declined"
