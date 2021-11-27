# UpsilonConf

UpsilonConf is a simple configuration library written in Python.
It might not be really obvious, but this library is inspired by the great [OmegaConf](https://github.com/omry/omegaconf) library.
Concretely, the idea of this library is to provide an alternative to OmegaConf without the overhead of the variable interpolation (especially the `antlr` dependency).
It is also very similar to the (discontinued) [AttrDict](https://github.com/bcj/AttrDict) library.

The name is obviously inspired by OmegaConf.
I chose to go for the Greek letter [Upsilon](https://en.wikipedia.org/wiki/Upsilon) because it is the first letter of [ὑπέρ (hupér)](https://en.wiktionary.org/wiki/ὑπέρ).
This again comes from the fact that this library should mainly help me with managing _hyper_-parameters in neural networks.
