# Stand-in for Ruby's bigdecimal extension, which this Ruby 2.5 install lacks.
# Liquid only uses it in math filters (round, divided_by, ...) that the site does not use.
class BigDecimal < Numeric; end
module Kernel
  def BigDecimal(value, *_)
    Float(value)
  end
end
