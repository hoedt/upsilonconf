# UpsilonConf

UpsilonConf is a simple configuration library written in Python.
It might not be really obvious, but this library is inspired by the great [OmegaConf](https://github.com/omry/omegaconf) library.
Concretely, the idea of this library is to provide an alternative to OmegaConf without the overhead of the variable interpolation (especially the `antlr` dependency).
It is also very similar to the (discontinued) [AttrDict](https://github.com/bcj/AttrDict) library.
It turns out that the [`ml_collections`](https://github.com/google/ml_collections) library pretty much covers everything I had in mind(and a bit more) for the configuration stuff (except for flexible config file formats, maybe).
Therefore, this project might be superfluous from it's infancy, but I'll leave it hanging for some time.

The name is obviously inspired by OmegaConf.
I chose to go for the Greek letter [Upsilon](https://en.wikipedia.org/wiki/Upsilon) because it is the first letter of [ὑπέρ (hupér)](https://en.wiktionary.org/wiki/ὑπέρ).
This again comes from the fact that this library should mainly help me with managing _hyper_-parameters in neural networks.
