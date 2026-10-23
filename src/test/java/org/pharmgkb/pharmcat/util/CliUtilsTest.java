package org.pharmgkb.pharmcat.util;

import java.util.regex.Pattern;
import org.apache.commons.lang3.StringUtils;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;


/**
 * This is a JUnit test for {@link CliUtils}.
 *
 * @author Mark Woon
 */
class CliUtilsTest {
  private static final Pattern sf_versionPattern = Pattern.compile("^v\\d+\\.\\d+\\.\\d+(-\\d+-[a-z0-9]+)?$");

  @Test
  void testVersion() throws Exception {

    String version = StringUtils.stripToNull(CliUtils.getVersion());
    assertNotNull(version);
    System.out.println("Version: [" + version + "]");
    // Builds require a reachable release tag, including GitHub Actions checkouts.
    assertTrue(sf_versionPattern.matcher(version).matches(),
        "Expected a release-tagged version but got: " + version);
  }
}
