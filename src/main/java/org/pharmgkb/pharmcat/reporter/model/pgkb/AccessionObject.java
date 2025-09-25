
package org.pharmgkb.pharmcat.reporter.model.pgkb;

import com.google.gson.annotations.Expose;
import com.google.gson.annotations.SerializedName;


/**
 * General PharmGKB Accession Object Model
 */
public class AccessionObject {
  @Expose
  @SerializedName("id")
  private String id;
  @Expose
  @SerializedName("name")
  private String name;
  @Expose
  @SerializedName("symbol")
  private String symbol;
  @Expose
  @SerializedName("name_cn")
  private String nameCn;


  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public String getSymbol() {
    return symbol;
  }

  public void setSymbol(String symbol) {
    this.symbol = symbol;
  }

  public String getNameCn() {
    return nameCn;
  }

  public void setNameCn(String nameCn) {
    this.nameCn = nameCn;
  }

  /**
   * Gets the display name, preferring Chinese name if available, otherwise English name.
   */
  public String getDisplayName() {
    return nameCn != null && !nameCn.trim().isEmpty() ? nameCn : name;
  }
}
