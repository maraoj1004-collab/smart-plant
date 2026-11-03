#include <unity.h>
#include "rules.h"

void setUp() {}
void tearDown() {}

void test_dry_soil_waters() { TEST_ASSERT_EQUAL(WATER, decide({20, 25, 50, 800})); }
void test_hot() { TEST_ASSERT_EQUAL(ALERT_HOT, decide({50, 35, 50, 800})); }
void test_dark() { TEST_ASSERT_EQUAL(ALERT_DARK, decide({50, 25, 50, 100})); }
void test_ok() { TEST_ASSERT_EQUAL(NONE, decide({50, 25, 50, 800})); }
void test_water_has_priority() { TEST_ASSERT_EQUAL(WATER, decide({10, 40, 50, 50})); }
void test_boundary_not_dry() { TEST_ASSERT_EQUAL(NONE, decide({30, 32, 50, 200})); }
void test_action_names() {
  TEST_ASSERT_EQUAL_STRING("WATER", actionName(WATER));
  TEST_ASSERT_EQUAL_STRING("NONE", actionName(NONE));
}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_dry_soil_waters);
  RUN_TEST(test_hot);
  RUN_TEST(test_dark);
  RUN_TEST(test_ok);
  RUN_TEST(test_water_has_priority);
  RUN_TEST(test_boundary_not_dry);
  RUN_TEST(test_action_names);
  return UNITY_END();
}
