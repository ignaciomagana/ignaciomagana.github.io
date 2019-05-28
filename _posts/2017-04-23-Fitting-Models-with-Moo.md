---
layout: post
title:  "Fitting Models with MOO"
categories: journal
tags: [statistics]
image:
  feature: galaxy_header.jpg
  teaser: galaxy_header_teaser.jpg
  credit: Wikipedia Commons
  creditlink: ""
comments: true
---

This post summarizes a lecture I have given several times to undergrads and early graduate students on model fitting. I will (hopefully) highlight the flexibility of the fitting process and a simple guide to work through most problems. I'm going to assume a basic understanding of the statistics involved, and my example problem will be in Python.

## Using MOO <img src="/images/april2017/april2017_cow.png" alt="cow" style="width: 50px;"/>


Imagine I give you a dataset and I ask you to fit a model to it. This might be a supernova light curve, a stellar spectrum or a galaxy rotation model. Whatever problem you're facing, we can break it down into **MOO**: 
1. _**M**odel_ which you need to choose to fit to the data!
2. _**O**jective Function_ which is a metric that you will choose to quantify how *well* the model fits the data.
3. _**O**ptimization Method_ which you will use to pick the *best* model.

We're going to break down each step using a simple astronomical example. For each step, I'll provide code to solve the problem in a few ways, so I encourage you to mix-and-match!

## The Model

Let's start with an example **model** and dataset to fit. In astronomy, a common problem is to fit Gaussian-like models to [spectral lines](https://en.wikipedia.org/wiki/Spectral_line). These models typically have three parameters: height, width and central wavelength. You can play with two models in this example: the Lorentzian and the Gaussian. The Lorentzian profile looks like:

```python
def my_model(lam,center,height,width):
    return height * (width/2.)**2 / ((lam - center)**2 + (width/2.)**2)
```

and the Gaussian profile is:

```python
def my_model(lam,center,height,width):
    return height * np.exp(-0.5 * (lam - center)**2/width**2)
```

Choose the *right* model can be very challenging. In many cases, the model will be physically motivated. For example, we can think of a physical model to describe the light curve of a transiting planet. Other times, our models are *data-driven*. For example, the famous [M-sigma relation](https://en.wikipedia.org/wiki/M%E2%80%93sigma_relation) relates the stellar velocity dispersion of a galaxy bulge with the mass of its supermassive black hole. The physical basis of this relation is uncertain, but we can see that a linear model connects the two galactic features.

Back to our problem: I am going to generate some fake data which we can fit our model to by adding white ( uncorrelated) noise:

```python
my_lam = np.arange(6400,6700,1)
NOISE = 5.0
my_data = my_model(my_lam,6563,100,20) + np.random.normal(0, NOISE,len(my_lam))
my_sigmas = np.zeros(len(my_lam)) + NOISE
plt.plot(my_lam,my_data)
plt.xlabel(r'$\lambda$')
plt.ylabel('Flux')
plt.title('Beautiful Data')
plt.show()
```

![png](/images/april2017/banneker_3_0.png)

Our spectral line has a *true* height of 100 flux units, a width of 20 Angstrom and a central wavelength of 6563 Angstrom. You can play with the `NOISE` parameter to change the signal-to-noise of the data. Try setting it to something very large, like `NOISE = 50`!

## The Objective Function

Now that we have our models (and some data!), let's choose a **metric** to quantify how *well* our model fits our dataset. This metric has many names: objective function, cost function, loss function, utility function, etc. (I called it an **objective function** so I could draw a cow.) The metric that most people are familiar with is called **chi-squared**:

```python
def metric_chi2(theta,lam,data,sigmas):
    center, height, width = theta
    return np.sum((my_model(lam,center,height,width)-data)**2/(sigmas)**2)
```

Remember that we want to *minimize* chi-squared values to choose the best model. Chi-squared assumes that our noise is uncorrelated and Gaussian, which is true in many cases. But we can easily choose other objective functions:

```python
def metric_residuals(theta,lam,data,sigmas):
    center, height, width = theta
    return np.sum(np.abs(my_model(lam,center,height,width)-data))
```

```python
def metric_log_likelihood(theta,lam,data,sigmas):
    center, height, width = theta
    return -0.5*(np.sum((data-my_model(lam,center,height,width))**2/sigmas**2 + np.log(sigmas**2)))
```

`metric_residuals` computes the sum of the absolute values of the residuals of our model, and `metric_log_likelihood` computes the log likelihood of our model. Remember that we want to *maximize* the log likelihood, but we want to *minimize* sums of residuals.

## The Optimization Method

Finally, let's fit our data by choosing an _optimization method_ to optimize our _objective function_. We're going to start with the easiest thing we can think of and work our way up. First, let's literally just pick random values for the height, width and center of our spectral line. We'll choose values 50 times, and the *best* model will be our winner. this is called a *random grid search*:

```python
center_choices = np.random.uniform(low=6500, high=6600, size=50)
height_choices = np.random.uniform(low=80, high=120, size=50)
width_choices = np.random.uniform(low=10, high=30, size=50)

lowest_chi = np.inf
best_c = 0
best_h = 0
best_w = 0
for i,c in enumerate(center_choices):
    h = height_choices[i]
    w = width_choices[i]

    theta = [c,h,w]

    current_chi = metric_log_likelihood(theta,my_lam,my_data,my_sigmas)
    if current_chi < lowest_chi:
        best_c = c
        best_h = h
        best_w = w
        lowest_chi = current_chi

print "Chi2",lowest_chi / len(my_lam)
plt.plot(my_lam,my_data)
plt.plot(my_lam,my_model(my_lam,best_c,best_h,best_w))
plt.show()
```

    Chi2 2.89601950512



![png](/images/april2017/banneker_6_1.png)


Our reduced chi-squared is about 3, which is pretty bad. Let's try to do better! We will use `scipy`'s `minimize` function, which uses a form of *gradient descent* to minimize the objective function:

```python
from scipy.optimize import minimize
p0 = [6560,90,5]
bnds = ((6500, 6650), (0, None),(0,None))
res = minimize(metric_log_likelihood, x0=p0,args=(my_lam,my_data,my_sigmas), options={'gtol': 1e-3, 'disp': True},bounds=bnds)
plt.plot(my_lam,my_data)
plt.plot(my_lam,my_model(my_lam,res.x[0],res.x[1],res.x[2]))
plt.show()
print "Chi2",metric_chi2(res.x,my_lam,my_data,my_sigmas)/len(my_lam)
```


![png](/images/april2017/banneker_8_0.png)


    Chi2 1.02930073003


Great! Our reduced chi-squared value is about 1, which means that we've found a good fit to the data. Play around with combining different _objective functions_ and _optimization methods_. Is there any metric which seems to work best for this problem?

Unfortunately, we do not have error estimates on our models using these optimization methods with the code provided. We can use an even fancier optimization technique called a [Markov-Chain Monte Carlo](https://jeremykun.com/2015/04/06/markov-chain-monte-carlo-without-all-the-bullshit/) to estimate the best-fit model *and* error bars on the model parameters by sampling from our likelihood function. We'll use the popular [`emcee`](http://dan.iel.fm/emcee/current/):


```python
ndim, nwalkers = 3, 100
p0 = [6560,90,5]
pos = [p0 + np.random.randn(ndim) for i in range(nwalkers)]

sampler = emcee.EnsembleSampler(nwalkers, ndim, metric_log_likelihood, args=(my_lam, my_data, my_sigmas))
sampler.run_mcmc(pos, 1000)

samples = sampler.chain[:, 500:, :].reshape((-1, ndim))
corner.corner(samples, labels=["center", "height", "width"])
plt.show()

plt.plot(samples[:,0])
plt.xlabel('Iteration Number')
plt.ylabel('Height')
plt.title('A Sample Chain')
plt.show()

print "CENTER",np.percentile(samples[:,0],[16,50,84])
print "HEIGHT",np.percentile(samples[:,1],[16,50,84])
print "WIDTH",np.percentile(samples[:,2],[16,50,84])

```


![png](/images/april2017/banneker_9_0.png)



![png](/images/april2017/banneker_9_1.png)


    CENTER [ 6562.78917939  6562.96188268  6563.14312425]
    HEIGHT [ 100.46597986  102.28547484  103.99994744]
    WIDTH [ 19.37125165  19.84305208  20.3369578 ]

The `corner` plot shows the best-fit parameter posterior distributions (assuming uniform priors), which we have used to estimate both the best-fit values and the 1-sigma error bars. Below this plot is a sample chain from the MCMC that shows a walker traversing through the posterior. 

Try adding a nonuniform prior to the _objective function_. Does the MCMC produce different results?

## Conclusion

We fit our model! Again, I highly recommend switching out the **MOO** components for this example and understanding what effects this has on your final model. Each component of **MOO** has special considerations, but it's important to remember that *you* have the power to change each step to fit your needs!

So what should you do when faced with real data? My biggest recommendation to new researchers is to do the *easiest* thing first. Choose a simple model, objective function and optimization function. For example, I typically begin model fits by minimizing chi-squared with `minimizer`. 

{% if page.comments %}
<div id="disqus_thread"></div>
<script>

/**
*  RECOMMENDED CONFIGURATION VARIABLES: EDIT AND UNCOMMENT THE SECTION BELOW TO INSERT DYNAMIC VALUES FROM YOUR PLATFORM OR CMS.
*  LEARN WHY DEFINING THESE VARIABLES IS IMPORTANT: https://disqus.com/admin/universalcode/#configuration-variables*/
/*
var disqus_config = function () {
this.page.url = PAGE_URL;  // Replace PAGE_URL with your page's canonical URL variable
this.page.identifier = PAGE_IDENTIFIER; // Replace PAGE_IDENTIFIER with your page's unique identifier variable
};
*/
(function() { // DON'T EDIT BELOW THIS LINE
var d = document, s = d.createElement('script');
s.src = 'https://ashleyvillar-com.disqus.com/embed.js';
s.setAttribute('data-timestamp', +new Date());
(d.head || d.body).appendChild(s);
})();
</script>
<noscript>Please enable JavaScript to view the <a href="https://disqus.com/?ref_noscript">comments powered by Disqus.</a></noscript>
{% endif %}

